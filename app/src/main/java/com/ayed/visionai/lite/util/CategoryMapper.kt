package com.ayed.visionai.lite.util

import com.ayed.visionai.lite.domain.model.ObjectCategory

/**
 * Maps a free-form ML Kit label to a coarse semantic [ObjectCategory]. This is
 * what powers the "animal / food / vehicle / product" feature filters on top of
 * the generic on-device detectors — no extra model required.
 */
object CategoryMapper {

    private val animals = setOf(
        "cat", "dog", "bird", "horse", "cow", "sheep", "elephant", "bear",
        "zebra", "giraffe", "animal", "fish", "duck", "rabbit", "lion", "tiger",
        "monkey", "deer", "pet", "insect", "butterfly", "frog", "snake", "turtle"
    )

    private val food = setOf(
        "food", "fruit", "vegetable", "apple", "banana", "orange", "pizza",
        "cake", "bread", "sandwich", "burger", "drink", "coffee", "dish",
        "dessert", "meal", "snack", "salad", "rice", "pasta", "egg", "meat"
    )

    private val vehicles = setOf(
        "car", "truck", "bus", "motorcycle", "bicycle", "vehicle", "train",
        "airplane", "boat", "ship", "van", "scooter", "wheel", "tire"
    )

    private val products = setOf(
        "fashion good", "home good", "product", "furniture", "phone", "laptop",
        "computer", "tv", "monitor", "keyboard", "mouse", "bottle", "cup",
        "book", "clock", "watch", "bag", "shoe", "clothing", "appliance",
        "tool", "packaged goods", "electronic device"
    )

    private val plants = setOf("plant", "flower", "tree", "leaf", "grass")

    private val persons = setOf("person", "people", "human", "face", "man", "woman")

    fun map(label: String): ObjectCategory {
        val l = label.lowercase().trim()
        return when {
            persons.any { l.contains(it) } -> ObjectCategory.PERSON
            animals.any { l.contains(it) } -> ObjectCategory.ANIMAL
            food.any { l.contains(it) } -> ObjectCategory.FOOD
            vehicles.any { l.contains(it) } -> ObjectCategory.VEHICLE
            plants.any { l.contains(it) } -> ObjectCategory.PLANT
            products.any { l.contains(it) } -> ObjectCategory.PRODUCT
            else -> ObjectCategory.GENERIC
        }
    }
}
