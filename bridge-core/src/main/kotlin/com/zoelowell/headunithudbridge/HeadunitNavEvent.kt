package com.zoelowell.headunithudbridge

enum class HeadunitNavEvent(val wireValue: Int) {
    UNKNOWN(0),
    DEPART(1),
    NAME_CHANGE(2),
    SLIGHT_TURN(3),
    TURN(4),
    SHARP_TURN(5),
    UTURN(6),
    ONRAMP(7),
    OFFRAMP(8),
    FORK(9),
    MERGE(10),
    ROUNDABOUT_ENTER(11),
    ROUNDABOUT_EXIT(12),
    ROUNDABOUT_ENTER_AND_EXIT(13),
    STRAIGHT(14),
    FERRY_BOAT(16),
    FERRY_TRAIN(17),
    DESTINATION(18);

    companion object {
        fun fromWireValue(value: Int): HeadunitNavEvent {
            return entries.firstOrNull { it.wireValue == value } ?: UNKNOWN
        }
    }
}