package com.zoelowell.headunithudbridge

import android.Manifest
import android.os.PowerManager
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import org.junit.Assert.assertFalse
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class MainActivityPermissionActionsTest {
    @Test
    fun hidesPermissionActionButtonsWhenNoActionsAreNeeded() {
        val app = RuntimeEnvironment.getApplication()
        shadowOf(app).grantPermissions(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.BLUETOOTH_SCAN,
            Manifest.permission.BLUETOOTH_CONNECT,
            Manifest.permission.POST_NOTIFICATIONS
        )
        shadowOf(app.getSystemService(PowerManager::class.java))
            .setIgnoringBatteryOptimizations(app.packageName, true)

        val activity = Robolectric.buildActivity(MainActivity::class.java)
            .setup()
            .get()

        val visibleButtonTexts = activity.window.decorView
            .collectButtons()
            .filter { it.visibility == View.VISIBLE }
            .map { it.text.toString() }

        assertFalse(activity.getString(R.string.button_request_permissions) in visibleButtonTexts)
        assertFalse(activity.getString(R.string.button_allow_background) in visibleButtonTexts)
    }

    private fun View.collectButtons(): List<Button> {
        if (this is Button) {
            return listOf(this)
        }
        if (this !is ViewGroup) {
            return emptyList()
        }
        return buildList {
            for (index in 0 until childCount) {
                addAll(getChildAt(index).collectButtons())
            }
        }
    }
}
