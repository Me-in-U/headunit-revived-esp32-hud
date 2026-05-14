package com.zoelowell.headunithudbridge

enum class TurnSide(val wireValue: Int) {
    LEFT(1),
    RIGHT(2),
    UNSPECIFIED(3);

    companion object {
        fun fromWireValue(value: Int): TurnSide {
            return entries.firstOrNull { it.wireValue == value } ?: UNSPECIFIED
        }
    }
}