<#
.SYNOPSIS
    Git integration module.
.DESCRIPTION
    Detects Git, the current repository and branch, stages changes, creates a
    descriptive commit and pushes to the current branch. Authentication failures
    are handled gracefully and never cause credentials to be printed. If the
    working tree is not a git repository, the module reports this and does nothing.
#>

Set-StrictMode -Version Latest

function Test-GitAvailable {
    <#
    .SYNOPSIS
        Returns the git executable path, or $null if git is not installed.
    #>
    [CmdletBinding()]
    param()
    $cmd = Get-Command -Name git -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($base in @(${env:ProgramFiles}, ${env:ProgramFiles(x86)})) {
        if ([string]::IsNullOrWhiteSpace($base)) { continue }
        $p = Join-Path $base 'Git\cmd\git.exe'
        if (Test-Path -LiteralPath $p) { return $p }
    }
    return $null
}

function Invoke-Git {
    <#
    .SYNOPSIS
        Runs a git command in a repo directory and returns Output + ExitCode.
        stderr is captured to avoid leaking to the console (may contain URLs).
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string]   $GitExe,
        [Parameter(Mandatory = $true)] [string]   $RepoPath,
        [Parameter(Mandatory = $true)] [string[]] $GitArgs
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = $GitExe
    $psi.WorkingDirectory       = $RepoPath
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.UseShellExecute        = $false
    $psi.CreateNoWindow         = $true
    # Prevent git from launching interactive credential prompts that would hang.
    $psi.EnvironmentVariables['GIT_TERMINAL_PROMPT'] = '0'
    $psi.EnvironmentVariables['GCM_INTERACTIVE']     = 'never'
    foreach ($a in $GitArgs) { $psi.ArgumentList.Add($a) }

    $proc = [System.Diagnostics.Process]::Start($psi)
    $out  = $proc.StandardOutput.ReadToEnd()
    $err  = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()

    return @{ Output = $out.Trim(); Error = $err.Trim(); ExitCode = $proc.ExitCode }
}

function Get-GitContext {
    <#
    .SYNOPSIS
        Returns repository context: IsRepo, Branch, Remote, HasChanges.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $GitExe,
        [Parameter(Mandatory = $true)] [string] $RepoPath
    )

    $ctx = @{ IsRepo = $false; Branch = $null; Remote = $null; HasChanges = $false }

    $inside = Invoke-Git -GitExe $GitExe -RepoPath $RepoPath -GitArgs @('rev-parse','--is-inside-work-tree')
    if ($inside.ExitCode -ne 0 -or $inside.Output -ne 'true') { return $ctx }
    $ctx.IsRepo = $true

    # 'branch --show-current' (git 2.22+) reports the branch even on an unborn
    # HEAD (a freshly created branch with no commits yet); fall back as needed.
    $branch = Invoke-Git -GitExe $GitExe -RepoPath $RepoPath -GitArgs @('branch','--show-current')
    if ($branch.ExitCode -eq 0 -and $branch.Output) {
        $ctx.Branch = $branch.Output
    } else {
        $sym = Invoke-Git -GitExe $GitExe -RepoPath $RepoPath -GitArgs @('symbolic-ref','--short','HEAD')
        if ($sym.ExitCode -eq 0 -and $sym.Output) { $ctx.Branch = $sym.Output }
    }

    $remote = Invoke-Git -GitExe $GitExe -RepoPath $RepoPath -GitArgs @('remote')
    if ($remote.ExitCode -eq 0 -and $remote.Output) {
        $ctx.Remote = ($remote.Output -split "`n")[0].Trim()
    }

    $status = Invoke-Git -GitExe $GitExe -RepoPath $RepoPath -GitArgs @('status','--porcelain')
    $ctx.HasChanges = ($status.ExitCode -eq 0 -and $status.Output.Length -gt 0)

    return $ctx
}

function Invoke-GitCommitAndPush {
    <#
    .SYNOPSIS
        Stages all changes, commits with a descriptive message and pushes to the
        current branch with retry/backoff. Returns a result hashtable.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)] [string] $RepoPath,
        [Parameter(Mandatory = $true)] [string] $CommitMessage,
        [Parameter(Mandatory = $true)] [scriptblock] $Logger,
        [int] $MaxRetries = 4
    )

    $git = Test-GitAvailable
    if (-not $git) {
        & $Logger "Git is not installed; skipping repository integration." 'WARN'
        return @{ Success = $false; Message = 'git not found' }
    }

    $ctx = Get-GitContext -GitExe $git -RepoPath $RepoPath
    if (-not $ctx.IsRepo) {
        & $Logger "Not a git repository: $RepoPath. Skipping commit/push." 'WARN'
        return @{ Success = $false; Message = 'not a repo' }
    }

    & $Logger "Git repository detected. Branch: $($ctx.Branch); Remote: $($ctx.Remote)" 'INFO'

    if (-not $ctx.HasChanges) {
        & $Logger "No changes to commit." 'INFO'
        return @{ Success = $true; Message = 'nothing to commit' }
    }

    $add = Invoke-Git -GitExe $git -RepoPath $RepoPath -GitArgs @('add','-A')
    if ($add.ExitCode -ne 0) {
        & $Logger "git add failed: $($add.Error)" 'ERROR'
        return @{ Success = $false; Message = 'git add failed' }
    }

    $commit = Invoke-Git -GitExe $git -RepoPath $RepoPath -GitArgs @('commit','-m',$CommitMessage)
    if ($commit.ExitCode -ne 0) {
        # A non-zero here is usually "nothing to commit" after add; report and stop.
        & $Logger "git commit returned non-zero: $($commit.Output) $($commit.Error)" 'WARN'
        return @{ Success = $false; Message = 'commit failed or nothing staged' }
    }
    & $Logger "Committed changes to '$($ctx.Branch)'." 'SUCCESS'

    if (-not $ctx.Remote) {
        & $Logger "No remote configured; commit created locally only." 'WARN'
        return @{ Success = $true; Message = 'committed locally (no remote)' }
    }

    # Push with exponential backoff. Auth failures are detected and reported
    # without echoing any credential material.
    $delay = 2
    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
        $push = Invoke-Git -GitExe $git -RepoPath $RepoPath -GitArgs @('push','-u',$ctx.Remote,$ctx.Branch)
        if ($push.ExitCode -eq 0) {
            & $Logger "Pushed to $($ctx.Remote)/$($ctx.Branch)." 'SUCCESS'
            return @{ Success = $true; Message = 'pushed' }
        }

        $errLower = $push.Error.ToLower()
        if ($errLower -match 'authentication|could not read username|permission denied|403|terminal prompts disabled|invalid credentials') {
            & $Logger "Push failed due to authentication/permission. Configure a credential helper or token and retry. (No credentials were displayed.)" 'ERROR'
            return @{ Success = $false; Message = 'auth failure' }
        }

        if ($attempt -lt $MaxRetries) {
            & $Logger "Push attempt $attempt failed (network/other). Retrying in ${delay}s..." 'WARN'
            Start-Sleep -Seconds $delay
            $delay *= 2
        } else {
            & $Logger "Push failed after $MaxRetries attempts: $($push.Error)" 'ERROR'
        }
    }
    return @{ Success = $false; Message = 'push failed' }
}

Export-ModuleMember -Function Test-GitAvailable, Invoke-Git, Get-GitContext, Invoke-GitCommitAndPush
