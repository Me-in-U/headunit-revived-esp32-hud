package com.zoelowell.headunithudbridge

object ProgressTextAnimator {
    private const val DOT_INTERVAL_MILLIS = 500L
    private const val DOT_FIELD_WIDTH = 3
    private const val DOT_FRAME_COUNT = DOT_FIELD_WIDTH + 1
    private val progressMarkerPattern = Regex("""중\.{0,3}[ \t]{0,3}(?=\s|$|[·:.,])""")

    fun animate(text: String, nowMillis: Long = System.currentTimeMillis()): String {
        val dots = dotsFor(nowMillis)
        return progressMarkerPattern.replace(text) { "중$dots" }
    }

    fun dotsFor(nowMillis: Long = System.currentTimeMillis()): String {
        val frame = ((nowMillis / DOT_INTERVAL_MILLIS) % DOT_FRAME_COUNT).toInt()
        return ".".repeat(frame).padEnd(DOT_FIELD_WIDTH, ' ')
    }
}
