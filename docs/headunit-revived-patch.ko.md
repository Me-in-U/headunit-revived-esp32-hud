# Headunit Revived HUD Patch Guide

[프로젝트 README](../README.ko.md) | [Protocol reference](protocol.ko.md)

이 문서는 공식 Headunit Revived 버전이 바뀌었을 때 HUD bridge가 필요한 Headunit 쪽 변경을 빠르게 다시 적용하기 위한 재작업 가이드입니다.

HUD bridge는 Headunit Revived 내부 상태를 직접 읽지 않습니다. Headunit Revived가 Android Auto 내비게이션 상태를 `com.andrerinas.headunitrevived.NAVIGATION_UPDATE` 브로드캐스트로 내보내고, 이 저장소의 Android 앱이 그 브로드캐스트를 받아 ESP32 HUD UDP packet으로 변환합니다.

## 적용 대상

Headunit Revived repo:

- `contract/src/main/java/com/andrerinas/headunitrevived/contract/HeadUnitIntent.kt`
- `app/src/main/java/com/andrerinas/headunitrevived/aap/AapNavigationHelper.kt`
- `app/src/main/AndroidManifest.xml` 또는 broadcast 권한 정책이 있는 manifest/config 파일

HUD bridge repo의 대응 코드:

- `bridge-core/src/main/kotlin/com/zoelowell/headunithudbridge/HeadunitRevivedBroadcast.kt`
- `android-app/src/main/java/com/zoelowell/headunithudbridge/HeadunitNavigationIntentExtensions.kt`
- `bridge-core/src/main/kotlin/com/zoelowell/headunithudbridge/NavigationFreshnessGate.kt`
- `android-app/src/main/java/com/zoelowell/headunithudbridge/HudBridgeService.kt`

## 필요한 Headunit Contract

Headunit Revived는 다음 action을 implicit broadcast로 발행해야 합니다.

```text
com.andrerinas.headunitrevived.NAVIGATION_UPDATE
```

HUD bridge가 기대하는 주요 extra는 다음과 같습니다.

| Extra | Type | Required | Unknown value |
| --- | --- | --- | --- |
| `distance_meters` | int | yes | `-1` |
| `time_seconds` | int | yes | `-1` |
| `road` | string | yes | empty string 또는 `--` |
| `next_event_type` | int | yes | Headunit legacy unknown value |
| `action_text` | string | yes | empty string |
| `turn_side` | int | yes | `3` |
| `turn_number` | int | yes | `-1` |
| `turn_angle` | int | yes | `-1` |
| `total_distance_meters` | int | recommended | `-1` |
| `total_time_seconds` | long | recommended | `-1` |
| `estimated_arrival` | string | recommended | empty string |
| `cluster_age_ms` | long | recommended for stale filtering | `-1` |
| `turn_detail_age_ms` | long | recommended for stale filtering | `-1` |
| `turn_distance_age_ms` | long | recommended for stale filtering | `-1` |

`cluster_age_ms`, `turn_detail_age_ms`, `turn_distance_age_ms`는 표시 자체를 위한 필드는 아니지만 HUD bridge가 오래된 navigation snapshot을 다시 그리는 것을 막는 데 사용합니다. 값이 없으면 bridge는 `-1`을 unknown age로 보고 stale filtering을 약하게 적용합니다.

## HeadUnitIntent.kt 변경

`NavigationUpdateIntent` 생성자에 age field 3개를 기본값 있는 optional parameter로 추가합니다. 기존 caller와 binary/source compatibility를 최대한 유지하기 위해 새 parameter는 기존 parameter 뒤에 붙입니다.

기존 KDoc parameter 목록에는 다음 줄을 `estimatedArrival` 설명 뒤에 추가합니다.

```kotlin
 * @param clusterAgeMs Age in milliseconds for the last NavigationClusterStatus message, [EXTRA_CLUSTER_AGE_MS], or null.
 * @param turnDetailAgeMs Age in milliseconds for the last NextTurnDetail message, [EXTRA_TURN_DETAIL_AGE_MS], or null.
 * @param turnDistanceAgeMs Age in milliseconds for the last NextTurnDistanceEvent message, [EXTRA_TURN_DISTANCE_AGE_MS], or null.
```

```kotlin
class NavigationUpdateIntent(
    distanceMeters: Int?,
    timeSeconds: Int?,
    road: String,
    nextEventType: Int,
    actionText: String,
    turnSide: Int? = null,
    turnNumber: Int? = null,
    turnAngle: Int? = null,
    totalDistanceMeters: Int? = null,
    totalTimeSeconds: Long? = null,
    estimatedArrival: String? = null,
    clusterAgeMs: Long? = null,
    turnDetailAgeMs: Long? = null,
    turnDistanceAgeMs: Long? = null
) : Intent(action)
```

`init` block에는 negative 또는 null 값을 `-1L`로 normalize해서 넣습니다.

```kotlin
putExtra(EXTRA_CLUSTER_AGE_MS, clusterAgeMs?.takeIf { it >= 0 } ?: -1L)
putExtra(EXTRA_TURN_DETAIL_AGE_MS, turnDetailAgeMs?.takeIf { it >= 0 } ?: -1L)
putExtra(EXTRA_TURN_DISTANCE_AGE_MS, turnDistanceAgeMs?.takeIf { it >= 0 } ?: -1L)
```

`companion object`에는 stable extra name을 추가합니다.

```kotlin
/** Age in milliseconds for the last NavigationClusterStatus message, or -1 if not set. */
const val EXTRA_CLUSTER_AGE_MS = "cluster_age_ms"

/** Age in milliseconds for the last legacy NextTurnDetail message, or -1 if not set. */
const val EXTRA_TURN_DETAIL_AGE_MS = "turn_detail_age_ms"

/** Age in milliseconds for the last legacy NextTurnDistanceEvent message, or -1 if not set. */
const val EXTRA_TURN_DISTANCE_AGE_MS = "turn_distance_age_ms"
```

KDoc에도 constructor parameter와 constant 양쪽에 세 field의 의미를 남깁니다. 나중에 공식 Headunit Revived가 navigation contract를 바꿔도, 이 주석이 field의 freshness 용도를 바로 설명해야 합니다.

- `clusterAgeMs`: 마지막 `NavigationClusterStatus` snapshot age.
- `turnDetailAgeMs`: 마지막 legacy `NextTurnDetail` snapshot age.
- `turnDistanceAgeMs`: 마지막 legacy `NextTurnDistanceEvent` snapshot age.

## AapNavigationHelper.kt 변경

`FullNavigationMessage`에 age field 3개를 추가합니다.

```kotlin
val clusterAgeMs: Long?,
val turnDetailAgeMs: Long?,
val turnDistanceAgeMs: Long?
```

`sendFullNavigationBroadcast()`에서 `NavigationUpdateIntent`를 만들 때 age field를 그대로 전달합니다.

```kotlin
clusterAgeMs = prepared.clusterAgeMs,
turnDetailAgeMs = prepared.turnDetailAgeMs,
turnDistanceAgeMs = prepared.turnDistanceAgeMs
```

`prepareFullNavigationMessage()`에서 snapshot을 읽은 직후 현재 elapsed realtime을 잡습니다.

```kotlin
val now = nowElapsedRealtimeMs()
```

navigation message를 return하기 전에 각 snapshot age를 계산합니다.

```kotlin
val clusterAgeMs = ageMs(now, snapshot.clusterStatus)
val turnDetailAgeMs = ageMs(now, snapshot.nextTurnDetail)
val turnDistanceAgeMs = ageMs(now, snapshot.nextTurnDistance)
```

return object에 세 값을 포함합니다.

```kotlin
clusterAgeMs = clusterAgeMs,
turnDetailAgeMs = turnDetailAgeMs,
turnDistanceAgeMs = turnDistanceAgeMs
```

helper는 elapsed realtime 기준으로 음수가 되지 않게 clamp합니다.

```kotlin
private fun ageMs(now: Long, timedMessage: TimedMessage<*>?): Long? {
    return timedMessage?.updatedAtElapsedRealtimeMs?.let {
        (now - it).coerceAtLeast(0L)
    }
}
```

현재 patch에는 기능 변경과 함께 `actionText` local value의 들여쓰기 보정도 포함되어 있습니다. 공식 버전 재적용 중 같은 형태의 잘못된 들여쓰기나 block 밖으로 밀려난 것처럼 보이는 코드가 있으면, 아래처럼 `prepareFullNavigationMessage()` 내부 local value로 정리합니다.

```kotlin
val actionText = state?.stepsList?.firstOrNull()?.maneuver?.type?.let { maneuverTypeToAction(it) }
    ?: detail?.takeIf { it.hasNextTurn() }?.let { nextEventToAction(it.nextTurn) }
    ?: context.getString(R.string.nav_action_unknown)
```

기존 거리, 시간, 도로명, maneuver type, `turn_side` mapping은 유지합니다. HUD bridge는 localized `action_text`에서 좌우 방향을 추론하지 않고 `turn_side`와 event field를 우선 사용합니다.

## Broadcast 권한 확인

공식 Headunit Revived 버전이 바뀌면 가장 먼저 권한 정책을 확인합니다.

```powershell
rg -n "NAVIGATION_UPDATE|BROADCAST_PERMISSION|protectionLevel|sendBroadcast\\(intent" app contract
```

HUD bridge가 Headunit과 같은 signing key로 설치되지 않는다면 signature-only broadcast는 외부 bridge 앱에서 수신할 수 없습니다. 이 경우 다음 중 하나가 필요합니다.

- Headunit APK와 HUD Bridge APK를 같은 signing key로 빌드/설치합니다.
- Headunit의 navigation broadcast를 external companion app이 받을 수 있는 권한 정책으로 조정합니다.
- Headunit 내부에 bridge 송신 기능을 직접 넣습니다. 이 방식은 이 repo의 기본 방향인 companion app 구조와 다릅니다.

현재 companion app 구조에서는 `NAVIGATION_UPDATE`가 bridge 앱까지 도달하는 것이 필수입니다. ESP32 BLE provisioning이나 speed HUD는 일부 동작할 수 있지만, route guidance HUD는 이 broadcast 없이는 표시할 수 없습니다.

## 공식 버전 변경 시 재적용 절차

1. 공식 Headunit Revived 새 버전을 checkout합니다.
2. 아래 심볼을 찾습니다.

```powershell
rg -n "class NavigationUpdateIntent|sendFullNavigationBroadcast|NavigationSnapshot|TimedMessage|NavigationClusterStatus|NextTurnDetail|NextTurnDistanceEvent" .
```

3. 공식 코드가 이미 `cluster_age_ms`, `turn_detail_age_ms`, `turn_distance_age_ms` 또는 동등한 freshness field를 제공하는지 확인합니다.
4. 없으면 `HeadUnitIntent.kt`에 additive extra를 추가합니다.
5. `AapNavigationHelper.kt` 또는 새 navigation helper 위치에서 snapshot update timestamp를 기준으로 age를 계산해 broadcast에 넣습니다.
6. `sendBroadcast` 권한 정책이 bridge 앱 수신을 허용하는지 확인합니다.
7. HUD bridge repo에서 `HeadunitRevivedBroadcast.kt` extra name과 `HeadunitNavigationIntentExtensions.kt` parser가 Headunit contract와 일치하는지 확인합니다.
8. Headunit과 HUD Bridge를 같은 tablet에 설치하고 Android Auto route guidance로 runtime 수신을 확인합니다.

## 검증 명령

Headunit Revived 쪽:

```powershell
.\gradlew.bat :app:assembleDebug
```

HUD bridge 쪽:

```powershell
.\gradlew.bat :bridge-core:test :android-app:testDebugUnitTest :android-app:assembleDebug --warning-mode all
```

ESP32 firmware까지 같이 확인할 수 있으면:

```powershell
platformio run -d esp32-hud -e esp32-s3-n16r8
```

Runtime smoke check:

1. Headunit Revived와 HUD Bridge를 tablet에 설치합니다.
2. HUD Bridge foreground service를 시작합니다.
3. Android Auto projection과 route guidance를 시작합니다.
4. HUD Bridge dashboard가 `WAITING_FOR_BROADCAST`에서 `NAVIGATION_ACTIVE`로 바뀌는지 확인합니다.
5. ESP32 serial log 또는 OLED에서 다음 maneuver distance/road/icon이 갱신되는지 확인합니다.

## Codex 재적용 Prompt 예시

새 공식 Headunit Revived checkout에서 아래처럼 지시하면 됩니다.

```text
docs/headunit-revived-patch.ko.md를 기준으로 Headunit Revived의 HUD bridge navigation broadcast support를 다시 적용해줘.
변경은 additive하게 유지하고, NavigationUpdateIntent에 cluster_age_ms, turn_detail_age_ms, turn_distance_age_ms를 추가한 뒤 AapNavigationHelper의 snapshot timestamp로 age를 계산해서 broadcast에 넣어줘.
sendBroadcast 권한 정책이 별도 HUD Bridge 앱 수신을 막는지도 확인하고, 필요한 최소 수정과 검증 명령 결과를 정리해줘.
```

## 재적용 시 주의할 점

- Field rename/remove는 피합니다. HUD bridge와 ESP32 protocol은 additive compatibility를 전제로 합니다.
- `action_text`는 표시 text로만 보고 방향 판단에는 쓰지 않습니다.
- Age field는 wall-clock이 아니라 `SystemClock.elapsedRealtime()` 기준 timestamp 차이로 계산합니다.
- Unknown age는 `-1`로 내보냅니다.
- Official upstream이 navigation helper 구조를 바꿨다면 파일명보다 심볼과 데이터 흐름을 기준으로 찾습니다: AA navigation message 수신, snapshot 저장, debounced broadcast emission 순서입니다.
- 권한 문제는 코드가 맞아도 runtime에서 무음 실패처럼 보일 수 있으므로 반드시 별도 확인합니다.
