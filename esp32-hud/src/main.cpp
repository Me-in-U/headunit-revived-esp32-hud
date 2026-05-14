#include <Arduino.h>
#include <ArduinoJson.h>
#include <Adafruit_GFX.h>
#include <BLE2902.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <Preferences.h>
#include <Wire.h>
#include <WiFi.h>
#include <WiFiUdp.h>

#if __has_include("config.h")
#include "config.h"
#endif
#include "KoreanBitmapLabels.h"

#ifndef HUD_WIFI_SSID
#define HUD_WIFI_SSID ""
#endif
#ifndef HUD_WIFI_PASSWORD
#define HUD_WIFI_PASSWORD ""
#endif
#ifndef HUD_UDP_PORT
#define HUD_UDP_PORT 4210
#endif

#ifndef HUD_OLED_SDA
#define HUD_OLED_SDA 8
#endif
#ifndef HUD_OLED_SCL
#define HUD_OLED_SCL 9
#endif
#ifndef HUD_OLED_ADDRESS
#define HUD_OLED_ADDRESS 0x3C
#endif
#ifndef HUD_OLED_WIDTH
#define HUD_OLED_WIDTH 128
#endif
#ifndef HUD_OLED_HEIGHT
#define HUD_OLED_HEIGHT 64
#endif
#ifndef HUD_OLED_RESET
#define HUD_OLED_RESET -1
#endif
#ifndef HUD_OLED_DRIVER
#define HUD_OLED_DRIVER 1106
#endif
#ifndef HUD_OLED2_ENABLED
#define HUD_OLED2_ENABLED 1
#endif
#ifndef HUD_OLED2_SDA
#define HUD_OLED2_SDA 10
#endif
#ifndef HUD_OLED2_SCL
#define HUD_OLED2_SCL 11
#endif
#ifndef HUD_OLED2_ADDRESS
#define HUD_OLED2_ADDRESS 0x3C
#endif
#ifndef HUD_OLED2_RESET
#define HUD_OLED2_RESET -1
#endif

#if HUD_OLED_DRIVER == 1106
#include <Adafruit_SH110X.h>
#define HUD_OLED_BLACK SH110X_BLACK
#define HUD_OLED_WHITE SH110X_WHITE
using HudDisplay = Adafruit_SH1106G;
#else
#include <Adafruit_SSD1306.h>
#define HUD_OLED_BLACK SSD1306_BLACK
#define HUD_OLED_WHITE SSD1306_WHITE
using HudDisplay = Adafruit_SSD1306;
#endif

namespace {
constexpr char BLE_DEVICE_NAME[] = "Headunit HUD";
constexpr char BLE_SERVICE_UUID[] = "3f2d8a62-8b0f-4c0d-9d2b-7b71d831e001";
constexpr char BLE_WIFI_CREDENTIALS_UUID[] = "3f2d8a62-8b0f-4c0d-9d2b-7b71d831e002";
constexpr char BLE_STATUS_UUID[] = "3f2d8a62-8b0f-4c0d-9d2b-7b71d831e003";
constexpr uint16_t DEFAULT_UDP_PORT = HUD_UDP_PORT;
constexpr uint16_t DISCOVERY_PORT = 4211;
constexpr uint32_t WIFI_CONNECT_TIMEOUT_MS = 20000;
constexpr uint32_t DISPLAY_BOOT_SPLASH_MS = 900;
constexpr uint32_t STATUS_PROGRESS_DOT_INTERVAL_MS = 500;
constexpr uint32_t DISCOVERY_BEACON_INTERVAL_MS = 3000;
constexpr uint32_t BRIDGE_PACKET_TIMEOUT_MS = 3000;
constexpr uint32_t WIFI_RECONNECT_INITIAL_MS = 5000;
constexpr uint32_t WIFI_RECONNECT_MAX_MS = 60000;
constexpr char PACKET_TYPE_SPEED[] = "speed";
constexpr char PACKET_TYPE_SETTINGS[] = "settings";
constexpr char HUD_LANGUAGE_KO_CODE[] = "ko";
constexpr char HUD_LANGUAGE_EN_CODE[] = "en";
constexpr uint8_t DEFAULT_SPEED_FONT_SIZE = 4;
constexpr uint8_t MIN_SPEED_FONT_SIZE = 2;
constexpr uint8_t MAX_SPEED_FONT_SIZE = 6;
constexpr float SPEED_UNIT_GAP_RATIO = 0.08f;

constexpr int EVENT_SLIGHT_TURN = 3;
constexpr int EVENT_TURN = 4;
constexpr int EVENT_SHARP_TURN = 5;
constexpr int EVENT_UTURN = 6;
constexpr int EVENT_ONRAMP = 7;
constexpr int EVENT_OFFRAMP = 8;
constexpr int EVENT_FORK = 9;
constexpr int EVENT_MERGE = 10;
constexpr int EVENT_ROUNDABOUT_ENTER = 11;
constexpr int EVENT_ROUNDABOUT_EXIT = 12;
constexpr int EVENT_ROUNDABOUT_ENTER_AND_EXIT = 13;
constexpr int EVENT_STRAIGHT = 14;
constexpr int EVENT_DESTINATION = 18;
constexpr int TURN_SIDE_LEFT = 1;
constexpr int TURN_SIDE_RIGHT = 2;
constexpr int TURN_SIDE_UNSPECIFIED = 3;

enum HudLanguage : uint8_t {
    HUD_LANGUAGE_KO,
    HUD_LANGUAGE_EN
};

WiFiUDP udp;
WiFiUDP discoveryUdp;
Preferences preferences;
BLECharacteristic* statusCharacteristic = nullptr;
HudDisplay display(HUD_OLED_WIDTH, HUD_OLED_HEIGHT, &Wire, HUD_OLED_RESET);
#if HUD_OLED2_ENABLED
HudDisplay contextDisplay(HUD_OLED_WIDTH, HUD_OLED_HEIGHT, &Wire1, HUD_OLED2_RESET);
#endif

char packetBuffer[4096];
String pendingSsid;
String pendingPassword;
uint16_t pendingUdpPort = DEFAULT_UDP_PORT;
uint16_t activeUdpPort = DEFAULT_UDP_PORT;
String savedSsid;
String savedPassword;
uint16_t savedUdpPort = DEFAULT_UDP_PORT;
bool hasPendingWifiCredentials = false;
bool hasSavedWifiCredentials = false;
bool udpStarted = false;
bool discoveryStarted = false;
bool displayReady = false;
#if HUD_OLED2_ENABLED
bool contextDisplayReady = false;
#endif
bool debugOverlayEnabled = false;
bool speedUnitVisible = true;
uint8_t speedFontSize = DEFAULT_SPEED_FONT_SIZE;
HudLanguage hudLanguage = HUD_LANGUAGE_KO;
uint32_t lastDiscoveryBeaconAt = 0;
uint64_t lastHudPacketSequence = 0;
bool hasHudPacketSequence = false;
bool bridgePacketActive = false;
uint32_t lastBridgePacketAt = 0;

String lastDisplayState = "BOOT";
String lastDisplayIp;
String lastDisplayMessage = "Starting";
uint8_t lastStatusProgressDotCount = 0;
int lastHudDistanceMeters = -1;
int lastHudTimeSeconds = -1;
int lastHudTurnSide = TURN_SIDE_UNSPECIFIED;
int lastHudEventType = 0;
String lastHudRoad;
int lastHudRoadBitmapWidth = 0;
int lastHudRoadBitmapHeight = 0;
String lastHudRoadBitmapHex;
int lastHudIconBitmapWidth = 0;
int lastHudIconBitmapHeight = 0;
String lastHudIconBitmapHex;
bool lastHudActiveGuidance = false;
bool hasLastHud = false;
int lastSpeedKmh = -1;
bool hasSpeedValue = false;
bool wifiConnectedState = false;
uint32_t wifiReconnectDelayMs = WIFI_RECONNECT_INITIAL_MS;
uint32_t nextWifiReconnectAt = 0;

uint8_t clampSpeedFontSize(int value) {
    if (value < MIN_SPEED_FONT_SIZE) {
        return MIN_SPEED_FONT_SIZE;
    }
    if (value > MAX_SPEED_FONT_SIZE) {
        return MAX_SPEED_FONT_SIZE;
    }
    return static_cast<uint8_t>(value);
}

void drawCenteredText(Adafruit_GFX& target, const String& text, int16_t y, uint8_t size, uint16_t color = HUD_OLED_WHITE) {
    int16_t x1 = 0;
    int16_t y1 = 0;
    uint16_t w = 0;
    uint16_t h = 0;
    target.setTextSize(size);
    target.getTextBounds(text, 0, y, &x1, &y1, &w, &h);
    int16_t x = (HUD_OLED_WIDTH - static_cast<int16_t>(w)) / 2;
    if (x < 0) {
        x = 0;
    }
    target.setCursor(x, y);
    target.setTextColor(color);
    target.print(text);
}

void drawCenteredText(const String& text, int16_t y, uint8_t size, uint16_t color = HUD_OLED_WHITE) {
    if (!displayReady) {
        return;
    }
    drawCenteredText(display, text, y, size, color);
}

void drawCenteredTextInBounds(
    Adafruit_GFX& target,
    const String& text,
    int16_t left,
    int16_t width,
    int16_t y,
    uint8_t size,
    uint16_t color = HUD_OLED_WHITE
) {
    int16_t x1 = 0;
    int16_t y1 = 0;
    uint16_t textWidth = 0;
    uint16_t textHeight = 0;
    target.setTextSize(size);
    target.getTextBounds(text, 0, y, &x1, &y1, &textWidth, &textHeight);
    int16_t x = left + (width - static_cast<int16_t>(textWidth)) / 2;
    if (x < left) {
        x = left;
    }
    target.setCursor(x, y);
    target.setTextColor(color);
    target.print(text);
}

String fitAscii(const String& value, size_t maxChars) {
    String result;
    for (size_t i = 0; i < value.length() && result.length() < maxChars; i++) {
        char c = value.charAt(i);
        if (c >= 32 && c <= 126) {
            result += c;
        }
    }
    result.trim();
    return result;
}

int hexNibble(char c) {
    if (c >= '0' && c <= '9') {
        return c - '0';
    }
    if (c >= 'a' && c <= 'f') {
        return c - 'a' + 10;
    }
    if (c >= 'A' && c <= 'F') {
        return c - 'A' + 10;
    }
    return -1;
}

bool drawPackedMonoHexBitmap(
    Adafruit_GFX& target,
    int16_t x,
    int16_t y,
    int width,
    int height,
    const String& hex,
    uint16_t color = HUD_OLED_WHITE
) {
    if (width <= 0 || height <= 0 || width > HUD_OLED_WIDTH || height > HUD_OLED_HEIGHT) {
        return false;
    }
    const int bytesPerRow = (width + 7) / 8;
    const int requiredHexLength = bytesPerRow * height * 2;
    if (hex.length() < static_cast<unsigned int>(requiredHexLength)) {
        return false;
    }

    int hexIndex = 0;
    for (int row = 0; row < height; row++) {
        for (int byteX = 0; byteX < bytesPerRow; byteX++) {
            const int high = hexNibble(hex.charAt(hexIndex++));
            const int low = hexNibble(hex.charAt(hexIndex++));
            if (high < 0 || low < 0) {
                return false;
            }
            const int value = (high << 4) | low;
            for (int bit = 0; bit < 8; bit++) {
                const int pixelX = byteX * 8 + bit;
                if (pixelX < width && (value & (1 << (7 - bit))) != 0) {
                    target.drawPixel(x + pixelX, y + row, color);
                }
            }
        }
    }
    return true;
}

void drawRoadTextInBounds(
    Adafruit_GFX& target,
    const String& road,
    int16_t left,
    int16_t width,
    int16_t y
) {
    if (lastHudRoadBitmapWidth > 0 && lastHudRoadBitmapHeight > 0 && lastHudRoadBitmapHex.length() > 0) {
        int16_t bitmapX = left + (width - lastHudRoadBitmapWidth) / 2;
        if (bitmapX < left) {
            bitmapX = left;
        }
        if (drawPackedMonoHexBitmap(
                target,
                bitmapX,
                y,
                lastHudRoadBitmapWidth,
                lastHudRoadBitmapHeight,
                lastHudRoadBitmapHex
            )) {
            return;
        }
    }

    const String fallbackText = fitAscii(road, 12);
    if (fallbackText.length() > 0) {
        drawCenteredTextInBounds(target, fallbackText, left, width, y + 4, 1);
    }
}

String formatDistance(int distanceMeters) {
    if (distanceMeters < 0) {
        return "--";
    }
    if (distanceMeters < 1000) {
        return String(distanceMeters) + "m";
    }
    if (distanceMeters < 10000) {
        char buffer[8];
        snprintf(buffer, sizeof(buffer), "%.1fkm", distanceMeters / 1000.0);
        return String(buffer);
    }
    return String(distanceMeters / 1000) + "km";
}

String formatSpeedValue(int speedKmh) {
    if (speedKmh < 0) {
        return "--";
    }
    if (speedKmh > 999) {
        return "999";
    }
    return String(speedKmh);
}

String formatCompactTime(int timeSeconds) {
    if (timeSeconds < 0) {
        return "--";
    }
    if (timeSeconds < 100) {
        return String(timeSeconds) + "s";
    }
    return String((timeSeconds + 30) / 60) + "m";
}

String formatContextTimeValue(int timeSeconds) {
    if (timeSeconds < 0) {
        return "--";
    }
    if (timeSeconds < 100) {
        return String(timeSeconds);
    }
    return String((timeSeconds + 30) / 60);
}

HudKoreanLabel contextTimeUnitLabel(int timeSeconds) {
    if (timeSeconds >= 100) {
        return KO_LABEL_MINUTES;
    }
    return KO_LABEL_SECONDS;
}

int16_t styledTextWidth(Adafruit_GFX& target, const String& text, uint8_t size);
void drawStyledText(Adafruit_GFX& target, const String& text, int16_t x, int16_t y, uint8_t size);
void drawStyledCenteredText(Adafruit_GFX& target, const String& text, int16_t y, uint8_t size);
void drawStyledCenteredTextInBounds(
    Adafruit_GFX& target,
    const String& text,
    int16_t left,
    int16_t width,
    int16_t y,
    uint8_t size
);

HudKoreanLabel koreanActionLabel(int eventType, int turnSide) {
    if (eventType == EVENT_DESTINATION) {
        return KO_LABEL_DESTINATION;
    }
    if (eventType == EVENT_UTURN) {
        return KO_LABEL_UTURN;
    }
    if (eventType == EVENT_STRAIGHT) {
        return KO_LABEL_STRAIGHT;
    }
    if (eventType == EVENT_FORK) {
        return KO_LABEL_FORK;
    }
    if (eventType == EVENT_MERGE) {
        return KO_LABEL_MERGE;
    }
    if (eventType == EVENT_ONRAMP) {
        return KO_LABEL_ONRAMP;
    }
    if (eventType == EVENT_OFFRAMP) {
        return KO_LABEL_OFFRAMP;
    }
    if (
        eventType == EVENT_ROUNDABOUT_ENTER ||
        eventType == EVENT_ROUNDABOUT_EXIT ||
        eventType == EVENT_ROUNDABOUT_ENTER_AND_EXIT
    ) {
        return KO_LABEL_ROUNDABOUT;
    }
    if (turnSide == TURN_SIDE_LEFT) {
        return KO_LABEL_LEFT_TURN;
    }
    if (turnSide == TURN_SIDE_RIGHT) {
        return KO_LABEL_RIGHT_TURN;
    }
    if (eventType == EVENT_SLIGHT_TURN || eventType == EVENT_TURN || eventType == EVENT_SHARP_TURN) {
        return KO_LABEL_TURN;
    }
    return KO_LABEL_NAV;
}

const char* hudLanguageCode(HudLanguage language) {
    return language == HUD_LANGUAGE_EN ? HUD_LANGUAGE_EN_CODE : HUD_LANGUAGE_KO_CODE;
}

HudLanguage parseHudLanguage(const char* value, HudLanguage fallback) {
    if (strcmp(value, HUD_LANGUAGE_EN_CODE) == 0) {
        return HUD_LANGUAGE_EN;
    }
    if (strcmp(value, HUD_LANGUAGE_KO_CODE) == 0) {
        return HUD_LANGUAGE_KO;
    }
    return fallback;
}

const char* englishLabel(HudKoreanLabel label) {
    switch (label) {
        case KO_LABEL_RIGHT_TURN:
            return "RIGHT";
        case KO_LABEL_LEFT_TURN:
            return "LEFT";
        case KO_LABEL_TURN:
            return "TURN";
        case KO_LABEL_STRAIGHT:
            return "STRAIGHT";
        case KO_LABEL_UTURN:
            return "U-TURN";
        case KO_LABEL_DESTINATION:
            return "DEST";
        case KO_LABEL_ONRAMP:
            return "ON RAMP";
        case KO_LABEL_OFFRAMP:
            return "OFF RAMP";
        case KO_LABEL_FORK:
            return "FORK";
        case KO_LABEL_MERGE:
            return "MERGE";
        case KO_LABEL_ROUNDABOUT:
            return "ROUND";
        case KO_LABEL_NAV:
            return "NAV";
        case KO_LABEL_NEXT:
            return "NEXT";
        case KO_LABEL_SECONDS:
            return "sec";
        case KO_LABEL_MINUTES:
            return "min";
        case KO_LABEL_CONNECTED:
            return "connected";
        case KO_LABEL_WAITING:
            return "waiting";
        case KO_LABEL_SEARCHING:
            return "searching";
        case KO_LABEL_CONNECTION_FAILED:
            return "failed";
        case KO_LABEL_WIFI:
            return "WiFi";
        case KO_LABEL_HEADUNIT:
            return "Headunit";
        case KO_LABEL_BRIDGE:
            return "Bridge";
    }
    return "HUD";
}

int16_t textWidth(Adafruit_GFX& target, const String& text, uint8_t size) {
    int16_t x1 = 0;
    int16_t y1 = 0;
    uint16_t w = 0;
    uint16_t h = 0;
    target.setTextSize(size);
    target.getTextBounds(text, 0, 0, &x1, &y1, &w, &h);
    return static_cast<int16_t>(w);
}

int16_t hudLabelWidth(Adafruit_GFX& target, HudKoreanLabel label, uint8_t englishSize = 1) {
    if (hudLanguage == HUD_LANGUAGE_EN) {
        return textWidth(target, englishLabel(label), englishSize);
    }
    return koreanLabel(label).width;
}

bool hudLabelUsesProgressDots(HudKoreanLabel label) {
    return label == KO_LABEL_WAITING || label == KO_LABEL_SEARCHING;
}

uint8_t statusProgressDotCount(uint32_t now = millis()) {
    return static_cast<uint8_t>((now / STATUS_PROGRESS_DOT_INTERVAL_MS) % 4);
}

String statusProgressDots(uint8_t dotCount) {
    String dots;
    for (uint8_t i = 0; i < dotCount; ++i) {
        dots += '.';
    }
    while (dots.length() < 3) {
        dots += ' ';
    }
    return dots;
}

int16_t hudLabelWidthWithProgressDots(
    Adafruit_GFX& target,
    HudKoreanLabel label,
    uint8_t englishSize,
    uint8_t dotCount
) {
    int16_t width = hudLabelWidth(target, label, englishSize);
    if (hudLabelUsesProgressDots(label)) {
        width += textWidth(target, "...", englishSize);
    }
    return width;
}

void drawKoreanLabel(Adafruit_GFX& target, HudKoreanLabel label, int16_t x, int16_t y, uint16_t color = HUD_OLED_WHITE) {
    const HudBitmapLabel& bitmapLabel = koreanLabel(label);
    target.drawBitmap(x, y, bitmapLabel.bitmap, bitmapLabel.width, bitmapLabel.height, color);
}

void drawHudLabel(
    Adafruit_GFX& target,
    HudKoreanLabel label,
    int16_t x,
    int16_t y,
    uint16_t color = HUD_OLED_WHITE,
    uint8_t englishSize = 1
) {
    if (hudLanguage == HUD_LANGUAGE_EN) {
        target.setTextSize(englishSize);
        target.setTextColor(color);
        target.setCursor(x, y);
        target.print(englishLabel(label));
        return;
    }
    drawKoreanLabel(target, label, x, y, color);
}

void drawHudLabelWithProgressDots(
    Adafruit_GFX& target,
    HudKoreanLabel label,
    int16_t x,
    int16_t y,
    uint16_t color,
    uint8_t englishSize,
    uint8_t dotCount
) {
    drawHudLabel(target, label, x, y, color, englishSize);
    if (!hudLabelUsesProgressDots(label)) {
        return;
    }

    target.setTextSize(englishSize);
    target.setTextColor(color);
    target.setCursor(x + hudLabelWidth(target, label, englishSize), y);
    target.print(statusProgressDots(dotCount));
}

void drawCenteredHudLabelWithProgressDots(
    Adafruit_GFX& target,
    HudKoreanLabel label,
    int16_t y,
    uint16_t color,
    uint8_t englishSize,
    uint8_t dotCount
) {
    const int16_t width = hudLabelWidthWithProgressDots(target, label, englishSize, dotCount);
    int16_t x = (HUD_OLED_WIDTH - width) / 2;
    if (x < 0) {
        x = 0;
    }
    drawHudLabelWithProgressDots(target, label, x, y, color, englishSize, dotCount);
}

void drawCenteredHudLabelInBounds(
    Adafruit_GFX& target,
    HudKoreanLabel label,
    int16_t left,
    int16_t width,
    int16_t y,
    uint16_t color = HUD_OLED_WHITE,
    uint8_t englishSize = 1
) {
    const int16_t labelWidth = hudLabelWidth(target, label, englishSize);
    int16_t x = left + (width - labelWidth) / 2;
    if (x < left) {
        x = left;
    }
    drawHudLabel(target, label, x, y, color, englishSize);
}

int16_t hudLabelUnitYOffset(uint8_t valueSize) {
    if (hudLanguage == HUD_LANGUAGE_EN) {
        return valueSize >= 3 ? 10 : 5;
    }
    return valueSize >= 3 ? 7 : 2;
}

void drawCenteredHudLabel(
    Adafruit_GFX& target,
    HudKoreanLabel label,
    int16_t y,
    uint16_t color = HUD_OLED_WHITE,
    uint8_t englishSize = 1
) {
    const int16_t width = hudLabelWidth(target, label, englishSize);
    int16_t x = (HUD_OLED_WIDTH - width) / 2;
    if (x < 0) {
        x = 0;
    }
    drawHudLabel(target, label, x, y, color, englishSize);
}

void drawCenteredKoreanLabel(Adafruit_GFX& target, HudKoreanLabel label, int16_t y, uint16_t color = HUD_OLED_WHITE) {
    const HudBitmapLabel& bitmapLabel = koreanLabel(label);
    int16_t x = (HUD_OLED_WIDTH - bitmapLabel.width) / 2;
    if (x < 0) {
        x = 0;
    }
    drawKoreanLabel(target, label, x, y, color);
}

void drawCenteredKoreanLabelInBounds(
    Adafruit_GFX& target,
    HudKoreanLabel label,
    int16_t left,
    int16_t width,
    int16_t y,
    uint16_t color = HUD_OLED_WHITE
) {
    const HudBitmapLabel& bitmapLabel = koreanLabel(label);
    int16_t x = left + (width - bitmapLabel.width) / 2;
    if (x < left) {
        x = left;
    }
    drawKoreanLabel(target, label, x, y, color);
}

void drawHeader(Adafruit_GFX& target, const String& mode, const String& rightText) {
    target.fillRect(0, 0, HUD_OLED_WIDTH, 11, HUD_OLED_WHITE);
    target.setTextSize(1);
    target.setTextColor(HUD_OLED_BLACK);
    target.setCursor(3, 2);
    target.print(mode);
    int16_t x1 = 0;
    int16_t y1 = 0;
    uint16_t w = 0;
    uint16_t h = 0;
    target.getTextBounds(rightText, 0, 0, &x1, &y1, &w, &h);
    target.setCursor(HUD_OLED_WIDTH - static_cast<int16_t>(w) - 3, 2);
    target.print(rightText);
    target.setTextColor(HUD_OLED_WHITE);
}

void drawHeader(const String& mode, const String& rightText) {
    drawHeader(display, mode, rightText);
}

void drawWideLine(
    Adafruit_GFX& target,
    int16_t x0,
    int16_t y0,
    int16_t x1,
    int16_t y1,
    uint8_t width,
    uint16_t color = HUD_OLED_WHITE
) {
    const int8_t radius = width / 2;
    const bool steep = abs(y1 - y0) > abs(x1 - x0);
    for (int8_t offset = -radius; offset <= radius; offset++) {
        if (steep) {
            target.drawLine(x0 + offset, y0, x1 + offset, y1, color);
        } else {
            target.drawLine(x0, y0 + offset, x1, y1 + offset, color);
        }
    }
    target.fillCircle(x0, y0, radius, color);
    target.fillCircle(x1, y1, radius, color);
}

constexpr uint8_t ICON_STEM_WIDTH = 11;
constexpr uint8_t ICON_CURVE_WIDTH = 11;
constexpr int16_t ICON_STEM_HALF = ICON_STEM_WIDTH / 2;

void drawVerticalStem(Adafruit_GFX& target, int16_t centerX, int16_t topY, int16_t bottomY) {
    target.fillRect(centerX - ICON_STEM_HALF, topY, ICON_STEM_WIDTH, bottomY - topY + 1, HUD_OLED_WHITE);
}

void drawHorizontalStem(Adafruit_GFX& target, int16_t x0, int16_t centerY, int16_t x1) {
    if (x1 < x0) {
        const int16_t temp = x0;
        x0 = x1;
        x1 = temp;
    }
    target.fillRect(x0, centerY - ICON_STEM_HALF, x1 - x0 + 1, ICON_STEM_WIDTH, HUD_OLED_WHITE);
}

void drawDiagonalArrowHead(Adafruit_GFX& target, int16_t x, int16_t y, int turnSide);

void drawCurvedBranchArrowIcon(Adafruit_GFX& target, int16_t x, int16_t y, int turnSide) {
    const bool right = turnSide == TURN_SIDE_RIGHT;
    const int16_t stemX = right ? x + 14 : x + 36;
    const int16_t bendX = right ? x + 22 : x + 28;
    const int16_t headBaseX = right ? x + 32 : x + 18;

    drawVerticalStem(target, stemX, y + 28, y + 37);
    drawWideLine(target, stemX, y + 28, bendX, y + 19, ICON_CURVE_WIDTH, HUD_OLED_WHITE);
    drawWideLine(target, bendX, y + 19, headBaseX, y + 14, ICON_CURVE_WIDTH, HUD_OLED_WHITE);
    target.fillCircle(stemX, y + 28, ICON_STEM_HALF, HUD_OLED_WHITE);
    target.fillCircle(bendX, y + 19, ICON_STEM_HALF, HUD_OLED_WHITE);

    drawDiagonalArrowHead(target, right ? x + 45 : x + 5, y + 5, turnSide);
}

void drawUpArrowHead(Adafruit_GFX& target, int16_t x, int16_t y) {
    target.fillTriangle(x, y, x - 15, y + 18, x + 15, y + 18, HUD_OLED_WHITE);
}

void drawDownArrowHead(Adafruit_GFX& target, int16_t x, int16_t y) {
    target.fillTriangle(x, y, x - 15, y - 18, x + 15, y - 18, HUD_OLED_WHITE);
}

void drawHorizontalArrowHead(Adafruit_GFX& target, int16_t x, int16_t y, int turnSide) {
    if (turnSide == TURN_SIDE_RIGHT) {
        target.fillTriangle(x, y, x - 17, y - 16, x - 17, y + 16, HUD_OLED_WHITE);
    } else {
        target.fillTriangle(x, y, x + 17, y - 16, x + 17, y + 16, HUD_OLED_WHITE);
    }
}

void drawDiagonalArrowHead(Adafruit_GFX& target, int16_t x, int16_t y, int turnSide) {
    if (turnSide == TURN_SIDE_RIGHT) {
        target.fillTriangle(x, y, x - 18, y + 3, x - 7, y + 19, HUD_OLED_WHITE);
    } else {
        target.fillTriangle(x, y, x + 18, y + 3, x + 7, y + 19, HUD_OLED_WHITE);
    }
}

void drawStraightIcon(Adafruit_GFX& target, int16_t x, int16_t y) {
    drawVerticalStem(target, x + 25, y + 17, y + 37);
    drawUpArrowHead(target, x + 25, y + 2);
}

void drawTurnIcon(Adafruit_GFX& target, int16_t x, int16_t y, int turnSide) {
    const bool right = turnSide == TURN_SIDE_RIGHT;
    const int16_t stemX = right ? x + 14 : x + 36;
    const int16_t endX = right ? x + 45 : x + 5;
    const int16_t cornerY = y + 18;
    drawVerticalStem(target, stemX, cornerY, y + 37);
    drawHorizontalStem(target, right ? stemX : x + 17, cornerY, right ? x + 33 : stemX);
    target.fillCircle(stemX, cornerY, ICON_STEM_HALF, HUD_OLED_WHITE);
    drawHorizontalArrowHead(target, endX, cornerY, turnSide);
}

void drawSlightTurnIcon(Adafruit_GFX& target, int16_t x, int16_t y, int turnSide) {
    const bool right = turnSide == TURN_SIDE_RIGHT;
    const int16_t bendX = right ? x + 30 : x + 20;
    const int16_t headBaseX = right ? x + 35 : x + 15;
    drawVerticalStem(target, x + 25, y + 28, y + 37);
    drawWideLine(target, x + 25, y + 28, bendX, y + 20, ICON_CURVE_WIDTH, HUD_OLED_WHITE);
    drawWideLine(target, bendX, y + 20, headBaseX, y + 14, ICON_CURVE_WIDTH, HUD_OLED_WHITE);
    target.fillCircle(x + 25, y + 28, ICON_STEM_HALF, HUD_OLED_WHITE);
    target.fillCircle(bendX, y + 20, ICON_STEM_HALF, HUD_OLED_WHITE);
    drawDiagonalArrowHead(target, right ? x + 45 : x + 5, y + 5, turnSide);
}

void drawSharpTurnIcon(Adafruit_GFX& target, int16_t x, int16_t y, int turnSide) {
    const bool right = turnSide == TURN_SIDE_RIGHT;
    const int16_t stemX = right ? x + 14 : x + 36;
    const int16_t endX = right ? x + 45 : x + 5;
    const int16_t cornerY = y + 11;
    drawVerticalStem(target, stemX, cornerY, y + 37);
    drawHorizontalStem(target, right ? stemX : x + 17, cornerY, right ? x + 33 : stemX);
    target.fillCircle(stemX, cornerY, ICON_STEM_HALF, HUD_OLED_WHITE);
    drawHorizontalArrowHead(target, endX, cornerY, turnSide);
}

void drawLeftArrowIcon(Adafruit_GFX& target, int16_t x, int16_t y) {
    drawTurnIcon(target, x, y, TURN_SIDE_LEFT);
}

void drawRightArrowIcon(Adafruit_GFX& target, int16_t x, int16_t y) {
    drawTurnIcon(target, x, y, TURN_SIDE_RIGHT);
}

void drawKeepIcon(Adafruit_GFX& target, int16_t x, int16_t y, int turnSide) {
    const bool right = turnSide == TURN_SIDE_RIGHT;
    const int16_t bendX = right ? x + 31 : x + 19;
    const int16_t headBaseX = right ? x + 35 : x + 15;
    drawVerticalStem(target, x + 25, y + 28, y + 37);
    drawWideLine(target, x + 25, y + 28, bendX, y + 20, ICON_CURVE_WIDTH, HUD_OLED_WHITE);
    drawWideLine(target, bendX, y + 20, headBaseX, y + 14, ICON_CURVE_WIDTH, HUD_OLED_WHITE);
    target.fillCircle(x + 25, y + 28, ICON_STEM_HALF, HUD_OLED_WHITE);
    target.fillCircle(bendX, y + 20, ICON_STEM_HALF, HUD_OLED_WHITE);
    drawDiagonalArrowHead(target, right ? x + 45 : x + 5, y + 5, turnSide);
}

void drawForkIcon(Adafruit_GFX& target, int16_t x, int16_t y, int turnSide) {
    if (turnSide == TURN_SIDE_LEFT || turnSide == TURN_SIDE_RIGHT) {
        drawCurvedBranchArrowIcon(target, x, y, turnSide);
        return;
    }

    drawStraightIcon(target, x, y);
}

void drawMergeIcon(Adafruit_GFX& target, int16_t x, int16_t y, int turnSide) {
    if (turnSide == TURN_SIDE_LEFT || turnSide == TURN_SIDE_RIGHT) {
        const bool right = turnSide == TURN_SIDE_RIGHT;
        const int16_t startX = right ? x + 43 : x + 7;
        drawWideLine(target, startX, y + 37, x + 25, y + 23, ICON_CURVE_WIDTH, HUD_OLED_WHITE);
        drawVerticalStem(target, x + 25, y + 17, y + 37);
        target.fillCircle(x + 25, y + 23, ICON_STEM_HALF, HUD_OLED_WHITE);
        drawUpArrowHead(target, x + 25, y + 2);
        return;
    }

    drawStraightIcon(target, x, y);
}

void drawOnRampIcon(Adafruit_GFX& target, int16_t x, int16_t y, int turnSide) {
    if (turnSide == TURN_SIDE_LEFT || turnSide == TURN_SIDE_RIGHT) {
        const bool right = turnSide == TURN_SIDE_RIGHT;
        const int16_t startX = right ? x + 43 : x + 7;
        drawWideLine(target, startX, y + 37, x + 25, y + 23, ICON_CURVE_WIDTH, HUD_OLED_WHITE);
        drawVerticalStem(target, x + 25, y + 17, y + 37);
        target.fillCircle(x + 25, y + 23, ICON_STEM_HALF, HUD_OLED_WHITE);
        drawUpArrowHead(target, x + 25, y + 2);
    } else {
        drawStraightIcon(target, x, y);
    }
}

void drawOffRampIcon(Adafruit_GFX& target, int16_t x, int16_t y, int turnSide) {
    if (turnSide == TURN_SIDE_LEFT || turnSide == TURN_SIDE_RIGHT) {
        drawCurvedBranchArrowIcon(target, x, y, turnSide);
    } else {
        drawStraightIcon(target, x, y);
    }
}

void drawUTurnIcon(Adafruit_GFX& target, int16_t x, int16_t y) {
    drawVerticalStem(target, x + 36, y + 13, y + 37);
    drawHorizontalStem(target, x + 16, y + 13, x + 36);
    drawVerticalStem(target, x + 16, y + 13, y + 26);
    target.fillCircle(x + 36, y + 13, ICON_STEM_HALF, HUD_OLED_WHITE);
    target.fillCircle(x + 16, y + 13, ICON_STEM_HALF, HUD_OLED_WHITE);
    target.fillTriangle(x + 16, y + 39, x + 4, y + 28, x + 28, y + 28, HUD_OLED_WHITE);
}

void drawDestinationIcon(Adafruit_GFX& target, int16_t x, int16_t y) {
    drawVerticalStem(target, x + 25, y + 28, y + 37);
    target.fillCircle(x + 25, y + 16, 14, HUD_OLED_WHITE);
    target.fillCircle(x + 25, y + 16, 8, HUD_OLED_BLACK);
    target.fillCircle(x + 25, y + 16, 4, HUD_OLED_WHITE);
}

void drawRoundaboutIcon(Adafruit_GFX& target, int16_t x, int16_t y) {
    drawVerticalStem(target, x + 25, y + 29, y + 37);
    target.fillCircle(x + 25, y + 18, 15, HUD_OLED_WHITE);
    target.fillCircle(x + 25, y + 18, 9, HUD_OLED_BLACK);
    target.drawCircle(x + 25, y + 18, 11, HUD_OLED_WHITE);
    target.drawCircle(x + 25, y + 18, 12, HUD_OLED_WHITE);
    drawHorizontalArrowHead(target, x + 45, y + 16, TURN_SIDE_RIGHT);
}

void drawManeuverIcon(Adafruit_GFX& target, int eventType, int turnSide, int16_t x, int16_t y) {
    if (eventType == EVENT_DESTINATION) {
        drawDestinationIcon(target, x, y);
    } else if (eventType == EVENT_UTURN) {
        drawUTurnIcon(target, x, y);
    } else if (
        eventType == EVENT_ROUNDABOUT_ENTER ||
        eventType == EVENT_ROUNDABOUT_EXIT ||
        eventType == EVENT_ROUNDABOUT_ENTER_AND_EXIT
    ) {
        drawRoundaboutIcon(target, x, y);
    } else if (eventType == EVENT_FORK) {
        drawForkIcon(target, x, y, turnSide);
    } else if (eventType == EVENT_ONRAMP) {
        drawOnRampIcon(target, x, y, turnSide);
    } else if (eventType == EVENT_OFFRAMP) {
        drawOffRampIcon(target, x, y, turnSide);
    } else if (eventType == EVENT_MERGE) {
        drawMergeIcon(target, x, y, turnSide);
    } else if (eventType == EVENT_STRAIGHT && turnSide == TURN_SIDE_LEFT) {
        drawKeepIcon(target, x, y, TURN_SIDE_LEFT);
    } else if (eventType == EVENT_STRAIGHT && turnSide == TURN_SIDE_RIGHT) {
        drawKeepIcon(target, x, y, TURN_SIDE_RIGHT);
    } else if (eventType == EVENT_SLIGHT_TURN && turnSide == TURN_SIDE_LEFT) {
        drawSlightTurnIcon(target, x, y, TURN_SIDE_LEFT);
    } else if (eventType == EVENT_SLIGHT_TURN && turnSide == TURN_SIDE_RIGHT) {
        drawSlightTurnIcon(target, x, y, TURN_SIDE_RIGHT);
    } else if (eventType == EVENT_SHARP_TURN && turnSide == TURN_SIDE_LEFT) {
        drawSharpTurnIcon(target, x, y, TURN_SIDE_LEFT);
    } else if (eventType == EVENT_SHARP_TURN && turnSide == TURN_SIDE_RIGHT) {
        drawSharpTurnIcon(target, x, y, TURN_SIDE_RIGHT);
    } else if (turnSide == TURN_SIDE_LEFT) {
        drawLeftArrowIcon(target, x, y);
    } else if (turnSide == TURN_SIDE_RIGHT) {
        drawRightArrowIcon(target, x, y);
    } else {
        drawStraightIcon(target, x, y);
    }
}

void drawManeuverIcon(int eventType, int turnSide, int16_t x, int16_t y) {
    drawManeuverIcon(display, eventType, turnSide, x, y);
}

bool drawLastHudIconBitmap(Adafruit_GFX& target, int16_t x, int16_t y) {
    if (lastHudIconBitmapWidth <= 0 || lastHudIconBitmapHeight <= 0 || lastHudIconBitmapHex.length() == 0) {
        return false;
    }
    return drawPackedMonoHexBitmap(
        target,
        x,
        y,
        lastHudIconBitmapWidth,
        lastHudIconBitmapHeight,
        lastHudIconBitmapHex
    );
}

void drawHudManeuverIcon(Adafruit_GFX& target, int eventType, int turnSide, int16_t x, int16_t y) {
    if (drawLastHudIconBitmap(target, x, y)) {
        return;
    }
    drawManeuverIcon(target, eventType, turnSide, x, y);
}

HudKoreanLabel statusDetailLabel(const String& state) {
    if (state == "connected") {
        return KO_LABEL_CONNECTED;
    }
    if (state == "connecting") {
        return KO_LABEL_SEARCHING;
    }
    if (state == "failed") {
        return KO_LABEL_CONNECTION_FAILED;
    }
    return KO_LABEL_WAITING;
}

void renderSpeedHudScreen();

void renderCenteredStatusLabel(HudDisplay& target, HudKoreanLabel label) {
    const uint8_t dotCount = statusProgressDotCount();
    lastStatusProgressDotCount = dotCount;
    target.clearDisplay();
    target.setTextColor(HUD_OLED_WHITE);
    drawCenteredHudLabelWithProgressDots(target, label, 23, HUD_OLED_WHITE, 2, dotCount);
    target.display();
}

void renderTwoLineStatusLabels(HudDisplay& target, HudKoreanLabel title, HudKoreanLabel detail) {
    const uint8_t dotCount = statusProgressDotCount();
    lastStatusProgressDotCount = dotCount;
    target.clearDisplay();
    target.setTextColor(HUD_OLED_WHITE);
    drawCenteredHudLabelWithProgressDots(target, title, 13, HUD_OLED_WHITE, 2, dotCount);
    drawCenteredHudLabelWithProgressDots(target, detail, 37, HUD_OLED_WHITE, 2, dotCount);
    target.display();
}

void renderSplitStatusScreens(HudKoreanLabel primaryLabel, HudKoreanLabel contextLabel) {
#if HUD_OLED2_ENABLED
    if (displayReady) {
        renderCenteredStatusLabel(display, primaryLabel);
    }
    if (contextDisplayReady) {
        renderCenteredStatusLabel(contextDisplay, contextLabel);
    } else if (displayReady) {
        renderTwoLineStatusLabels(display, primaryLabel, contextLabel);
    }
#else
    if (displayReady) {
        renderTwoLineStatusLabels(display, primaryLabel, contextLabel);
    }
#endif
}

void renderBridgeWaitingScreens() {
    renderSplitStatusScreens(KO_LABEL_BRIDGE, KO_LABEL_WAITING);
}

void renderHeadunitWaitingScreens() {
    if (displayReady) {
        if (hasSpeedValue) {
            renderSpeedHudScreen();
        } else {
            renderCenteredStatusLabel(display, KO_LABEL_HEADUNIT);
        }
    }

#if HUD_OLED2_ENABLED
    if (contextDisplayReady) {
        renderTwoLineStatusLabels(contextDisplay, KO_LABEL_HEADUNIT, KO_LABEL_WAITING);
    } else if (displayReady && hasSpeedValue) {
        renderTwoLineStatusLabels(display, KO_LABEL_HEADUNIT, KO_LABEL_WAITING);
    }
#endif
}

void renderWifiStatusScreens(const String& state) {
    renderSplitStatusScreens(KO_LABEL_WIFI, statusDetailLabel(state));
}

void drawContextTimePanel(Adafruit_GFX& target, int timeSeconds, int16_t labelY, int16_t valueY, uint8_t valueSize) {
    const String timeText = formatContextTimeValue(timeSeconds);
    const bool hasUnit = timeSeconds >= 0;
    const HudKoreanLabel unitLabel = contextTimeUnitLabel(timeSeconds);
    const int16_t unitGap = valueSize >= 3 ? 8 : 6;

    const int16_t textWidth = styledTextWidth(target, timeText, valueSize);

    int16_t totalWidth = textWidth;
    if (hasUnit) {
        totalWidth += unitGap + hudLabelWidth(target, unitLabel);
    }

    int16_t x = (HUD_OLED_WIDTH - totalWidth) / 2;
    if (x < 0) {
        x = 0;
    }

    target.setTextColor(HUD_OLED_WHITE);
    drawCenteredHudLabel(target, KO_LABEL_NEXT, labelY);
    drawStyledText(target, timeText, x, valueY, valueSize);

    if (hasUnit) {
        const int16_t unitY = valueY + hudLabelUnitYOffset(valueSize);
        drawHudLabel(target, unitLabel, x + textWidth + unitGap, unitY);
    }
}

uint8_t speedTextSizeFor(const String& speedText) {
    uint8_t size = clampSpeedFontSize(speedFontSize);
    if (speedText.length() >= 3 && size > 4) {
        size = 4;
    }
    return size;
}

int16_t speedTextWidth(const String& text, uint8_t size) {
    const int16_t cellWidth = 6 * size;
    const int16_t gap = size;
    return static_cast<int16_t>(text.length()) * cellWidth +
        static_cast<int16_t>(text.length() > 0 ? text.length() - 1 : 0) * gap;
}

int16_t speedUnitGap(uint8_t speedSize) {
    int16_t gap = static_cast<int16_t>((8 * speedSize) * SPEED_UNIT_GAP_RATIO + 0.5f);
    return gap > 0 ? gap : 1;
}

int16_t speedDigitCoord(int16_t origin, int16_t span, float ratio) {
    return origin + static_cast<int16_t>(span * ratio + 0.5f);
}

bool isStyledGlyph(char value) {
    return (value >= '0' && value <= '9') ||
        value == 'm' ||
        value == 'k' ||
        value == 'h' ||
        value == '/' ||
        value == '.' ||
        value == ':';
}

float styledGlyphAdvanceRatio(char value) {
    switch (value) {
        case 'm':
            return 0.96f;
        case '/':
        case '.':
        case ':':
            return 0.34f;
        default:
            return 0.72f;
    }
}

int16_t styledGlyphWidth(char value, uint8_t size) {
    const int16_t glyphHeight = 8 * size;
    return static_cast<int16_t>(glyphHeight * styledGlyphAdvanceRatio(value) + 0.5f);
}

bool isDistanceUnitChar(char value) {
    return value == 'm' || value == 'k' || value == 'h';
}

int16_t styledGlyphGap(char current, char next, uint8_t size) {
    const int16_t glyphHeight = 8 * size;
    int16_t gap = 0;
    if (current != '.' && next != '.' && current != ':' && next != ':') {
        gap += static_cast<int16_t>(glyphHeight * 0.06f + 0.5f);
    }
    if (current >= '0' && current <= '9' && isDistanceUnitChar(next)) {
        gap += static_cast<int16_t>(glyphHeight * 0.12f + 0.5f);
    }
    return gap;
}

void drawSpeedDigitSegment(
    Adafruit_GFX& target,
    int16_t x,
    int16_t y,
    int16_t cellWidth,
    int16_t glyphHeight,
    uint8_t strokeWidth,
    float startX,
    float startY,
    float endX,
    float endY
) {
    drawWideLine(
        target,
        speedDigitCoord(x, cellWidth, startX),
        speedDigitCoord(y, glyphHeight, startY),
        speedDigitCoord(x, cellWidth, endX),
        speedDigitCoord(y, glyphHeight, endY),
        strokeWidth,
        HUD_OLED_WHITE
    );
}

void drawSpeedDigit(Adafruit_GFX& target, char digit, int16_t x, int16_t y, uint8_t size) {
    const int16_t cellWidth = styledGlyphWidth(digit, size);
    const int16_t glyphHeight = 8 * size;
    const uint8_t strokeWidth = size;
    auto segment = [&](float startX, float startY, float endX, float endY) {
        drawSpeedDigitSegment(target, x, y, cellWidth, glyphHeight, strokeWidth, startX, startY, endX, endY);
    };

    const auto top = [&]() { segment(0.16f, 0.07f, 0.84f, 0.07f); };
    const auto upperLeft = [&]() { segment(0.16f, 0.08f, 0.16f, 0.46f); };
    const auto upperRight = [&]() { segment(0.84f, 0.08f, 0.84f, 0.46f); };
    const auto middle = [&]() { segment(0.19f, 0.50f, 0.81f, 0.50f); };
    const auto lowerLeft = [&]() { segment(0.16f, 0.54f, 0.16f, 0.92f); };
    const auto lowerRight = [&]() { segment(0.84f, 0.54f, 0.84f, 0.92f); };
    const auto bottom = [&]() { segment(0.16f, 0.93f, 0.84f, 0.93f); };

    switch (digit) {
        case '0':
            top(); upperLeft(); upperRight(); lowerLeft(); lowerRight(); bottom();
            break;
        case '1':
            segment(0.60f, 0.08f, 0.60f, 0.92f);
            break;
        case '2':
            top(); upperRight(); middle(); lowerLeft(); bottom();
            break;
        case '3':
            top(); upperRight(); middle(); lowerRight(); bottom();
            break;
        case '4':
            upperLeft(); upperRight(); middle(); lowerRight();
            break;
        case '5':
            top(); upperLeft(); middle(); lowerRight(); bottom();
            break;
        case '6':
            top(); upperLeft(); middle(); lowerLeft(); lowerRight(); bottom();
            break;
        case '7':
            top();
            segment(0.84f, 0.07f, 0.84f, 0.26f);
            segment(0.84f, 0.26f, 0.30f, 0.93f);
            break;
        case '8':
            top(); upperLeft(); upperRight(); middle(); lowerLeft(); lowerRight(); bottom();
            break;
        case '9':
            top(); upperLeft(); upperRight(); middle(); lowerRight(); bottom();
            break;
        case 'm':
            segment(0.14f, 0.93f, 0.14f, 0.44f);
            segment(0.14f, 0.44f, 0.42f, 0.44f);
            segment(0.42f, 0.44f, 0.42f, 0.93f);
            segment(0.42f, 0.44f, 0.70f, 0.44f);
            segment(0.70f, 0.44f, 0.70f, 0.93f);
            break;
        case 'k':
            segment(0.18f, 0.08f, 0.18f, 0.93f);
            segment(0.80f, 0.37f, 0.22f, 0.62f);
            segment(0.33f, 0.58f, 0.84f, 0.93f);
            break;
        case 'h':
            segment(0.18f, 0.08f, 0.18f, 0.93f);
            segment(0.18f, 0.48f, 0.76f, 0.48f);
            segment(0.76f, 0.48f, 0.76f, 0.93f);
            break;
        case '/':
            segment(0.86f, 0.08f, 0.14f, 0.93f);
            break;
        case '.':
            segment(0.50f, 0.92f, 0.50f, 0.92f);
            break;
        case ':':
            segment(0.50f, 0.36f, 0.50f, 0.36f);
            segment(0.50f, 0.74f, 0.50f, 0.74f);
            break;
        default:
            break;
    }
}

String singleCharString(char value) {
    String text;
    text += value;
    return text;
}

int16_t defaultCharWidth(Adafruit_GFX& target, char value, uint8_t size) {
    int16_t x1 = 0;
    int16_t y1 = 0;
    uint16_t w = 0;
    uint16_t h = 0;
    const String text = singleCharString(value);
    target.setTextSize(size);
    target.getTextBounds(text, 0, 0, &x1, &y1, &w, &h);
    return w > 0 ? static_cast<int16_t>(w) : static_cast<int16_t>(6 * size);
}

int16_t styledTextWidth(Adafruit_GFX& target, const String& text, uint8_t size) {
    int16_t width = 0;
    for (uint16_t i = 0; i < text.length(); ++i) {
        const char value = text[i];
        width += isStyledGlyph(value) ? styledGlyphWidth(value, size) : defaultCharWidth(target, value, size);
        if (i + 1 < text.length()) {
            width += styledGlyphGap(value, text[i + 1], size);
        }
    }
    return width;
}

void drawStyledText(Adafruit_GFX& target, const String& text, int16_t x, int16_t y, uint8_t size) {
    int16_t cursorX = x;
    for (uint16_t i = 0; i < text.length(); ++i) {
        const char value = text[i];
        if (isStyledGlyph(value)) {
            drawSpeedDigit(target, value, cursorX, y, size);
            cursorX += styledGlyphWidth(value, size);
        } else {
            const String glyph = singleCharString(value);
            target.setTextSize(size);
            target.setCursor(cursorX, y);
            target.print(glyph);
            cursorX += defaultCharWidth(target, value, size);
        }
        if (i + 1 < text.length()) {
            cursorX += styledGlyphGap(value, text[i + 1], size);
        }
    }
}

void drawStyledCenteredText(Adafruit_GFX& target, const String& text, int16_t y, uint8_t size) {
    int16_t x = (HUD_OLED_WIDTH - styledTextWidth(target, text, size)) / 2;
    if (x < 0) {
        x = 0;
    }
    drawStyledText(target, text, x, y, size);
}

void drawStyledCenteredTextInBounds(
    Adafruit_GFX& target,
    const String& text,
    int16_t left,
    int16_t width,
    int16_t y,
    uint8_t size
) {
    int16_t x = left + (width - styledTextWidth(target, text, size)) / 2;
    if (x < left) {
        x = left;
    }
    drawStyledText(target, text, x, y, size);
}

void drawSpeedText(Adafruit_GFX& target, const String& text, int16_t x, int16_t y, uint8_t size) {
    const int16_t glyphHeight = 8 * size;
    const int16_t cellWidth = 6 * size;
    const int16_t gap = size;
    int16_t cursorX = x;
    for (uint16_t i = 0; i < text.length(); ++i) {
        drawSpeedDigit(target, text[i], cursorX, y, size);
        cursorX += cellWidth + gap;
    }
}

void renderSpeedHudScreen() {
    if (!displayReady) {
        return;
    }

    const String speedText = formatSpeedValue(lastSpeedKmh);
    const uint8_t speedSize = speedTextSizeFor(speedText);
    const int16_t speedWidth = speedTextWidth(speedText, speedSize);
    const uint8_t unitSize = 1;
    const String unitText = "km/h";
    const int16_t unitWidth = speedUnitVisible ? styledTextWidth(display, unitText, unitSize) : 0;
    const int16_t unitGap = speedUnitVisible ? speedUnitGap(speedSize) : 0;
    const int16_t totalWidth = speedWidth + (speedUnitVisible ? unitGap + unitWidth : 0);
    int16_t speedX = (HUD_OLED_WIDTH - totalWidth) / 2;
    if (speedX < 0) {
        speedX = 0;
    }
    const int16_t speedY = (HUD_OLED_HEIGHT - 8 * speedSize) / 2;
    const int16_t unitX = speedX + speedWidth + unitGap;
    const int16_t unitY = speedY + 8 * speedSize - 8 * unitSize;

    display.clearDisplay();
    display.setTextColor(HUD_OLED_WHITE);

    if (debugOverlayEnabled) {
        drawHeader("SPD", WiFi.isConnected() ? WiFi.localIP().toString() : "NO WIFI");
    }

    drawSpeedText(display, speedText, speedX, speedY, speedSize);

    if (speedUnitVisible) {
        drawStyledText(display, unitText, unitX, unitY, unitSize);
    }

    display.display();
}

void renderStatusScreen(const String& state, const String& ip, const String& message) {
    lastDisplayState = state;
    lastDisplayIp = ip;
    lastDisplayMessage = message;
    (void)ip;
    (void)message;

    if (state == "connected") {
        renderBridgeWaitingScreens();
        return;
    }
    renderWifiStatusScreens(state);
}

bool currentStatusScreenCanAnimate() {
    if (lastDisplayState == "connecting" || lastDisplayState == "idle" || lastDisplayState == "BLE READY") {
        return true;
    }
    if (lastDisplayState == "connected") {
        return !bridgePacketActive && !hasSpeedValue;
    }
    return false;
}

void handleStatusAnimation() {
    if (!currentStatusScreenCanAnimate()) {
        return;
    }

    const uint8_t dotCount = statusProgressDotCount();
    if (dotCount == lastStatusProgressDotCount) {
        return;
    }

    renderStatusScreen(lastDisplayState, lastDisplayIp, lastDisplayMessage);
}

void renderNavigationHudScreen(int distanceMeters, int timeSeconds, int turnSide, int eventType, const String& road) {
#if HUD_OLED2_ENABLED
    if (!contextDisplayReady) {
        return;
    }

    (void)timeSeconds;
    const String distance = formatDistance(distanceMeters);

    contextDisplay.clearDisplay();
    contextDisplay.setTextColor(HUD_OLED_WHITE);

    if (debugOverlayEnabled) {
        drawHeader(contextDisplay, "NAV", WiFi.isConnected() ? WiFi.localIP().toString() : "NO WIFI");
    }

    constexpr int16_t textColumnLeft = 50;
    constexpr int16_t textColumnWidth = HUD_OLED_WIDTH - textColumnLeft;
    const uint8_t distanceSize = distance.length() > 4 ? 2 : 3;
    const int16_t iconY = debugOverlayEnabled ? 15 : 12;
    const int16_t distanceY = distanceSize >= 3
        ? (debugOverlayEnabled ? 11 : 8)
        : (debugOverlayEnabled ? 16 : 14);
    const int16_t roadY = debugOverlayEnabled ? 42 : 43;

    drawHudManeuverIcon(contextDisplay, eventType, turnSide, 3, iconY);
    drawStyledCenteredTextInBounds(contextDisplay, distance, textColumnLeft, textColumnWidth, distanceY, distanceSize);
    drawRoadTextInBounds(contextDisplay, road, textColumnLeft, textColumnWidth, roadY);

    contextDisplay.display();
#else
    (void)distanceMeters;
    (void)timeSeconds;
    (void)turnSide;
    (void)eventType;
    (void)road;
#endif
}

void renderIdleHudScreens() {
    renderHeadunitWaitingScreens();
}

void renderSingleHudScreen(int distanceMeters, int turnSide, int eventType, const String& road) {
    if (!displayReady) {
        return;
    }

    const String distance = formatDistance(distanceMeters);

    display.clearDisplay();
    display.setTextColor(HUD_OLED_WHITE);

    if (debugOverlayEnabled) {
        const uint8_t distanceSize = distance.length() > 5 ? 2 : 3;
        const int16_t distanceY = distanceSize >= 3 ? 11 : 16;

        drawHeader("NAV", WiFi.isConnected() ? WiFi.localIP().toString() : "NO WIFI");
        drawHudManeuverIcon(display, eventType, turnSide, 3, 15);

        drawStyledText(display, distance, 50, distanceY, distanceSize);

        drawRoadTextInBounds(display, road, 50, HUD_OLED_WIDTH - 50, 42);
    } else {
        drawHudManeuverIcon(display, eventType, turnSide, 5, 15);

        drawStyledText(display, distance, 55, distance.length() > 5 ? 15 : 11, distance.length() > 5 ? 2 : 3);

        drawRoadTextInBounds(display, road, 50, HUD_OLED_WIDTH - 50, 43);
    }
    display.display();
}

void renderContextHudScreen(int timeSeconds, const String& road) {
#if HUD_OLED2_ENABLED
    if (!contextDisplayReady) {
        return;
    }

    contextDisplay.clearDisplay();
    contextDisplay.setTextColor(HUD_OLED_WHITE);

    if (debugOverlayEnabled) {
        const String roadLine = fitAscii(road, 19);

        drawHeader(contextDisplay, "NAV", WiFi.isConnected() ? WiFi.localIP().toString() : "NO WIFI");
        drawContextTimePanel(contextDisplay, timeSeconds, 13, 36, 2);

        contextDisplay.drawFastHLine(0, 54, HUD_OLED_WIDTH, HUD_OLED_WHITE);
        contextDisplay.setTextSize(1);
        contextDisplay.setCursor(2, 56);
        contextDisplay.print(roadLine);
    } else {
        drawContextTimePanel(contextDisplay, timeSeconds, 4, 33, 3);
    }
    contextDisplay.display();
#else
    (void)timeSeconds;
    (void)road;
#endif
}

void renderHudScreenValues(
    bool activeGuidance,
    int distanceMeters,
    int timeSeconds,
    int turnSide,
    int eventType,
    const String& road
) {
    if (!activeGuidance) {
        renderIdleHudScreens();
        return;
    }

#if HUD_OLED2_ENABLED
    if (contextDisplayReady) {
        renderSpeedHudScreen();
        renderNavigationHudScreen(distanceMeters, timeSeconds, turnSide, eventType, road);
        return;
    }
#endif

    (void)timeSeconds;
    renderSingleHudScreen(distanceMeters, turnSide, eventType, road);
}

bool isActiveGuidancePacket(
    const JsonDocument& doc,
    int distanceMeters,
    int timeSeconds,
    int eventType
) {
    if (doc["active"].is<bool>()) {
        return doc["active"].as<bool>();
    }
    return eventType != 0 ||
        distanceMeters >= 0 ||
        timeSeconds >= 0;
}

bool shouldAcceptHudPacket(const JsonDocument& doc) {
    if (!doc["seq"].is<uint64_t>()) {
        return true;
    }

    const uint64_t sequence = doc["seq"].as<uint64_t>();
    if (hasHudPacketSequence && sequence <= lastHudPacketSequence) {
        Serial.printf(
            "Ignoring stale HUD packet seq=%llu last=%llu\n",
            static_cast<unsigned long long>(sequence),
            static_cast<unsigned long long>(lastHudPacketSequence)
        );
        return false;
    }

    lastHudPacketSequence = sequence;
    hasHudPacketSequence = true;
    return true;
}

bool hasReachedTime(uint32_t now, uint32_t target);

void markBridgePacketReceived() {
    bridgePacketActive = true;
    lastBridgePacketAt = millis();
}

void resetBridgePacketState() {
    bridgePacketActive = false;
    lastBridgePacketAt = 0;
    hasSpeedValue = false;
    hasLastHud = false;
    hasHudPacketSequence = false;
}

void handleBridgePacketTimeout() {
    if (!udpStarted || !bridgePacketActive) {
        return;
    }

    const uint32_t now = millis();
    if (!hasReachedTime(now, lastBridgePacketAt + BRIDGE_PACKET_TIMEOUT_MS)) {
        return;
    }

    resetBridgePacketState();
    renderBridgeWaitingScreens();
    Serial.println("Bridge packet timeout; waiting for bridge");
}

void renderHudScreen(const JsonDocument& doc) {
    lastHudDistanceMeters = doc["distance_meters"] | -1;
    lastHudTimeSeconds = doc["time_seconds"] | -1;
    lastHudTurnSide = doc["turn_side"] | TURN_SIDE_UNSPECIFIED;
    lastHudEventType = doc["event_type"] | 0;
    lastHudRoad = String(doc["road"] | "");
    lastHudRoadBitmapWidth = doc["road_bitmap_width"] | 0;
    lastHudRoadBitmapHeight = doc["road_bitmap_height"] | 0;
    lastHudRoadBitmapHex = String(doc["road_bitmap_hex"] | "");
    lastHudIconBitmapWidth = doc["icon_bitmap_width"] | 0;
    lastHudIconBitmapHeight = doc["icon_bitmap_height"] | 0;
    lastHudIconBitmapHex = String(doc["icon_bitmap_hex"] | "");
    lastHudActiveGuidance = isActiveGuidancePacket(
        doc,
        lastHudDistanceMeters,
        lastHudTimeSeconds,
        lastHudEventType
    );
    hasLastHud = true;

    renderHudScreenValues(
        lastHudActiveGuidance,
        lastHudDistanceMeters,
        lastHudTimeSeconds,
        lastHudTurnSide,
        lastHudEventType,
        lastHudRoad
    );
}

void setupDisplay() {
    Wire.begin(HUD_OLED_SDA, HUD_OLED_SCL);
#if HUD_OLED_DRIVER == 1106
    displayReady = display.begin(HUD_OLED_ADDRESS, true);
#else
    displayReady = display.begin(SSD1306_SWITCHCAPVCC, HUD_OLED_ADDRESS);
#endif
    if (!displayReady) {
        Serial.println("Primary OLED initialization failed");
    }

#if HUD_OLED2_ENABLED
    Wire1.begin(HUD_OLED2_SDA, HUD_OLED2_SCL);
#if HUD_OLED_DRIVER == 1106
    contextDisplayReady = contextDisplay.begin(HUD_OLED2_ADDRESS, true);
#else
    contextDisplayReady = contextDisplay.begin(SSD1306_SWITCHCAPVCC, HUD_OLED2_ADDRESS);
#endif
    if (!contextDisplayReady) {
        Serial.println("Context OLED initialization failed");
    }
#endif

    if (!displayReady
#if HUD_OLED2_ENABLED
        && !contextDisplayReady
#endif
    ) {
        return;
    }

    if (displayReady) {
        display.clearDisplay();
        display.setTextColor(HUD_OLED_WHITE);
        display.cp437(true);
        drawHeader("BOOT", "S3 HUD");
        drawCenteredText("HEADUNIT", 18, 2);
        drawCenteredText("HUD", 39, 2);
        display.display();
    }
#if HUD_OLED2_ENABLED
    if (contextDisplayReady) {
        contextDisplay.clearDisplay();
        contextDisplay.setTextColor(HUD_OLED_WHITE);
        contextDisplay.cp437(true);
        drawHeader(contextDisplay, "BOOT", "NAV");
        drawCenteredHudLabel(contextDisplay, KO_LABEL_NAV, 18, HUD_OLED_WHITE, 2);
        drawCenteredText(contextDisplay, "SECOND OLED", 43, 1);
        contextDisplay.display();
    }
#endif
    delay(DISPLAY_BOOT_SPLASH_MS);
    renderStatusScreen("BLE READY", "", "waiting for Wi-Fi");
}

const char* compactState(const char* state) {
    if (strcmp(state, "idle") == 0) {
        return "i";
    }
    if (strcmp(state, "connecting") == 0) {
        return "g";
    }
    if (strcmp(state, "connected") == 0) {
        return "c";
    }
    if (strcmp(state, "failed") == 0) {
        return "f";
    }
    return state;
}

void notifyStatus(const char* state, const String& ip, const String& message) {
    JsonDocument bleDoc;
    bleDoc["s"] = compactState(state);
    if (ip.length() > 0) {
        bleDoc["i"] = ip;
    }

    String bleBody;
    serializeJson(bleDoc, bleBody);
    Serial.printf("BLE status: state=%s ip=%s message=%s body=%s\n", state, ip.c_str(), message.c_str(), bleBody.c_str());
    renderStatusScreen(String(state), ip, message);

    if (statusCharacteristic == nullptr) {
        return;
    }

    statusCharacteristic->setValue(bleBody.c_str());
    statusCharacteristic->notify();
}

bool hasReachedTime(uint32_t now, uint32_t target) {
    return static_cast<int32_t>(now - target) >= 0;
}

void startDiscoveryUdp() {
    if (discoveryStarted) {
        discoveryUdp.stop();
        discoveryStarted = false;
    }

    discoveryUdp.begin(DISCOVERY_PORT);
    discoveryStarted = true;
    Serial.printf("Listening for ESP32 discovery on UDP port %u\n", DISCOVERY_PORT);
}

IPAddress subnetBroadcastAddress() {
    const IPAddress ip = WiFi.localIP();
    const IPAddress mask = WiFi.subnetMask();
    return IPAddress(
        ip[0] | static_cast<uint8_t>(~mask[0]),
        ip[1] | static_cast<uint8_t>(~mask[1]),
        ip[2] | static_cast<uint8_t>(~mask[2]),
        ip[3] | static_cast<uint8_t>(~mask[3])
    );
}

void sendDiscoveryBeacon(const IPAddress& targetAddress, uint16_t targetPort) {
    if (WiFi.status() != WL_CONNECTED || !discoveryStarted) {
        return;
    }

    JsonDocument doc;
    doc["type"] = "headunit_hud_hello";
    doc["name"] = BLE_DEVICE_NAME;
    doc["ip"] = WiFi.localIP().toString();
    doc["udp_port"] = activeUdpPort;

    String body;
    serializeJson(doc, body);
    discoveryUdp.beginPacket(targetAddress, targetPort);
    discoveryUdp.write(reinterpret_cast<const uint8_t*>(body.c_str()), body.length());
    discoveryUdp.endPacket();
}

void handleDiscoveryPackets() {
    if (!discoveryStarted) {
        return;
    }

    const int packetSize = discoveryUdp.parsePacket();
    if (packetSize <= 0) {
        return;
    }

    const int length = discoveryUdp.read(packetBuffer, sizeof(packetBuffer) - 1);
    if (length <= 0) {
        return;
    }
    packetBuffer[length] = '\0';

    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, packetBuffer);
    if (error) {
        Serial.printf("Invalid discovery packet: %s\n", error.c_str());
        return;
    }

    const char* type = doc["type"] | "";
    if (strcmp(type, "headunit_hud_discover") != 0) {
        return;
    }

    Serial.printf(
        "Discovery probe from %s:%u\n",
        discoveryUdp.remoteIP().toString().c_str(),
        discoveryUdp.remotePort()
    );
    sendDiscoveryBeacon(discoveryUdp.remoteIP(), discoveryUdp.remotePort());
}

void sendPeriodicDiscoveryBeacon() {
    if (!discoveryStarted || WiFi.status() != WL_CONNECTED) {
        return;
    }

    const uint32_t now = millis();
    if (now - lastDiscoveryBeaconAt < DISCOVERY_BEACON_INTERVAL_MS) {
        return;
    }

    lastDiscoveryBeaconAt = now;
    sendDiscoveryBeacon(IPAddress(255, 255, 255, 255), DISCOVERY_PORT);
    sendDiscoveryBeacon(subnetBroadcastAddress(), DISCOVERY_PORT);
}

void startUdp(uint16_t udpPort) {
    if (udpStarted) {
        udp.stop();
        udpStarted = false;
    }

    resetBridgePacketState();
    udp.begin(udpPort);
    udpStarted = true;
    activeUdpPort = udpPort;
    startDiscoveryUdp();
    Serial.printf("Listening for HUD UDP packets on port %u\n", udpPort);
}

void stopNetworkListeners() {
    if (udpStarted) {
        udp.stop();
        udpStarted = false;
    }
    if (discoveryStarted) {
        discoveryUdp.stop();
        discoveryStarted = false;
    }
    resetBridgePacketState();
}

void rememberWifiCredentials(const String& ssid, const String& password, uint16_t udpPort) {
    savedSsid = ssid;
    savedPassword = password;
    savedUdpPort = udpPort;
    hasSavedWifiCredentials = savedSsid.length() > 0;
}

void resetWifiReconnectBackoff() {
    wifiReconnectDelayMs = WIFI_RECONNECT_INITIAL_MS;
    nextWifiReconnectAt = 0;
}

void scheduleNextWifiReconnect(uint32_t now) {
    if (!hasSavedWifiCredentials) {
        nextWifiReconnectAt = 0;
        return;
    }

    nextWifiReconnectAt = now + wifiReconnectDelayMs;
    Serial.printf("Next Wi-Fi reconnect attempt in %lu ms\n", static_cast<unsigned long>(wifiReconnectDelayMs));
    wifiReconnectDelayMs = min(wifiReconnectDelayMs * 2, WIFI_RECONNECT_MAX_MS);
}

void markWifiConnected(uint16_t udpPort, const char* message) {
    const String ip = WiFi.localIP().toString();
    wifiConnectedState = true;
    resetWifiReconnectBackoff();
    Serial.printf("Wi-Fi connected. ESP32 IP: %s\n", ip.c_str());
    startUdp(udpPort);
    notifyStatus("connected", ip, message);
}

void beginWifiReconnectAttempt(uint32_t now) {
    if (!hasSavedWifiCredentials) {
        return;
    }

    notifyStatus("connecting", "", "Wi-Fi reconnecting");
    WiFi.mode(WIFI_STA);
    WiFi.begin(savedSsid.c_str(), savedPassword.c_str());
    Serial.printf("Wi-Fi reconnect attempt SSID: %s\n", savedSsid.c_str());
    scheduleNextWifiReconnect(now);
}

bool connectWifi(const String& ssid, const String& password, uint16_t udpPort) {
    rememberWifiCredentials(ssid, password, udpPort);
    notifyStatus("connecting", "", "joining Wi-Fi");

    WiFi.mode(WIFI_STA);
    WiFi.disconnect(false, true);
    delay(200);
    WiFi.begin(ssid.c_str(), password.c_str());

    Serial.printf("Connecting to Wi-Fi SSID: %s", ssid.c_str());
    const uint32_t startedAt = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startedAt < WIFI_CONNECT_TIMEOUT_MS) {
        delay(500);
        handleStatusAnimation();
        Serial.print(".");
    }
    Serial.println();

    if (WiFi.status() != WL_CONNECTED) {
        wifiConnectedState = false;
        stopNetworkListeners();
        notifyStatus("failed", "", "Wi-Fi connection timed out");
        Serial.println("Wi-Fi connection failed");
        scheduleNextWifiReconnect(millis());
        return false;
    }

    markWifiConnected(udpPort, "Wi-Fi connected");
    return true;
}

void saveWifiCredentials(const String& ssid, const String& password, uint16_t udpPort) {
    preferences.begin("hud-bridge", false);
    preferences.putString("ssid", ssid);
    preferences.putString("password", password);
    preferences.putUShort("udp_port", udpPort);
    preferences.end();
}

bool loadWifiCredentials(String& ssid, String& password, uint16_t& udpPort) {
    if (!preferences.begin("hud-bridge", false)) {
        ssid = HUD_WIFI_SSID;
        password = HUD_WIFI_PASSWORD;
        udpPort = DEFAULT_UDP_PORT;
        return ssid.length() > 0;
    }
    ssid = preferences.getString("ssid", HUD_WIFI_SSID);
    password = preferences.getString("password", HUD_WIFI_PASSWORD);
    udpPort = preferences.getUShort("udp_port", DEFAULT_UDP_PORT);
    preferences.end();
    return ssid.length() > 0;
}

void saveDebugOverlaySetting(bool enabled) {
    if (!preferences.begin("hud-bridge", false)) {
        return;
    }
    preferences.putBool("debug", enabled);
    preferences.end();
}

void saveSpeedUnitSetting(bool visible) {
    if (!preferences.begin("hud-bridge", false)) {
        return;
    }
    preferences.putBool("speed_unit", visible);
    preferences.end();
}

void saveSpeedFontSizeSetting(uint8_t size) {
    if (!preferences.begin("hud-bridge", false)) {
        return;
    }
    preferences.putUChar("speed_font", clampSpeedFontSize(size));
    preferences.end();
}

void saveHudLanguageSetting(HudLanguage language) {
    if (!preferences.begin("hud-bridge", false)) {
        return;
    }
    preferences.putString("language", hudLanguageCode(language));
    preferences.end();
}

void loadDisplaySettings() {
    if (!preferences.begin("hud-bridge", false)) {
        debugOverlayEnabled = false;
        speedUnitVisible = true;
        speedFontSize = DEFAULT_SPEED_FONT_SIZE;
        hudLanguage = HUD_LANGUAGE_KO;
        return;
    }
    debugOverlayEnabled = preferences.getBool("debug", false);
    speedUnitVisible = preferences.getBool("speed_unit", true);
    speedFontSize = clampSpeedFontSize(preferences.getUChar("speed_font", DEFAULT_SPEED_FONT_SIZE));
    hudLanguage = parseHudLanguage(preferences.getString("language", HUD_LANGUAGE_KO_CODE).c_str(), HUD_LANGUAGE_KO);
    preferences.end();
}

bool handleSettingsPacket(const JsonDocument& doc) {
    const char* type = doc["type"] | "";
    if (strcmp(type, PACKET_TYPE_SETTINGS) != 0) {
        return false;
    }

    debugOverlayEnabled = doc["debug_overlay"] | debugOverlayEnabled;
    speedUnitVisible = doc["speed_unit_visible"] | speedUnitVisible;
    speedFontSize = clampSpeedFontSize(doc["speed_font_size"] | speedFontSize);
    hudLanguage = parseHudLanguage(doc["language"] | hudLanguageCode(hudLanguage), hudLanguage);
    saveDebugOverlaySetting(debugOverlayEnabled);
    saveSpeedUnitSetting(speedUnitVisible);
    saveSpeedFontSizeSetting(speedFontSize);
    saveHudLanguageSetting(hudLanguage);
    Serial.printf(
        "Debug overlay: %s, speed unit: %s, speed font: %u, language: %s\n",
        debugOverlayEnabled ? "on" : "off",
        speedUnitVisible ? "on" : "off",
        speedFontSize,
        hudLanguageCode(hudLanguage)
    );

    if (hasLastHud) {
        renderHudScreenValues(
            lastHudActiveGuidance,
            lastHudDistanceMeters,
            lastHudTimeSeconds,
            lastHudTurnSide,
            lastHudEventType,
            lastHudRoad
        );
    } else {
        renderHeadunitWaitingScreens();
    }
    return true;
}

bool handleSpeedPacket(const JsonDocument& doc) {
    const char* type = doc["type"] | "";
    if (strcmp(type, PACKET_TYPE_SPEED) != 0) {
        return false;
    }

    lastSpeedKmh = doc["speed_kmh"] | -1;
    hasSpeedValue = true;
    Serial.printf("HUD speed=%d km/h\n", lastSpeedKmh);
    if (hasLastHud && lastHudActiveGuidance) {
        renderSpeedHudScreen();
    } else {
        renderHeadunitWaitingScreens();
    }
    return true;
}

void renderHudMessage(const JsonDocument& doc) {
    const char* instruction = doc["instruction"] | "경로 안내";
    int distanceMeters = doc["distance_meters"] | -1;
    int turnSide = doc["turn_side"] | TURN_SIDE_UNSPECIFIED;
    const char* road = doc["road"] | "";
    int roadBitmapWidth = doc["road_bitmap_width"] | 0;
    int iconBitmapWidth = doc["icon_bitmap_width"] | 0;

    Serial.printf(
        "HUD instruction=%s distance=%d side=%d road=%s roadBitmap=%d iconBitmap=%d\n",
        instruction,
        distanceMeters,
        turnSide,
        road,
        roadBitmapWidth,
        iconBitmapWidth
    );
    renderHudScreen(doc);
}

void handleUdpPackets() {
    if (!udpStarted) {
        delay(20);
        return;
    }

    int packetSize = udp.parsePacket();
    if (packetSize <= 0) {
        delay(20);
        return;
    }

    int length = udp.read(packetBuffer, sizeof(packetBuffer) - 1);
    if (length <= 0) {
        return;
    }
    packetBuffer[length] = '\0';

    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, packetBuffer);
    if (error) {
        Serial.printf("Invalid HUD packet: %s\n", error.c_str());
        return;
    }

    if (!shouldAcceptHudPacket(doc)) {
        return;
    }

    markBridgePacketReceived();

    if (handleSettingsPacket(doc)) {
        return;
    }
    if (handleSpeedPacket(doc)) {
        return;
    }

    renderHudMessage(doc);
}

void queueWifiCredentials(const String& body) {
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, body);
    if (error) {
        notifyStatus("failed", "", String("invalid credential JSON: ") + error.c_str());
        return;
    }

    const char* ssid = doc["ssid"] | "";
    const char* password = doc["password"] | "";
    uint16_t udpPort = doc["udp_port"] | DEFAULT_UDP_PORT;

    if (strlen(ssid) == 0) {
        notifyStatus("failed", "", "missing Wi-Fi SSID");
        return;
    }

    pendingSsid = ssid;
    pendingPassword = password;
    pendingUdpPort = udpPort;
    hasPendingWifiCredentials = true;
    notifyStatus("connecting", "", "credentials received");
}

class ProvisioningServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* server) override {
        notifyStatus("idle", WiFi.isConnected() ? WiFi.localIP().toString() : "", "BLE connected");
    }

    void onDisconnect(BLEServer* server) override {
        BLEDevice::startAdvertising();
        Serial.println("BLE disconnected; advertising restarted");
    }
};

class WifiCredentialsCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* characteristic) override {
        String body = characteristic->getValue().c_str();
        Serial.printf("Received Wi-Fi credentials packet: %s\n", body.c_str());
        queueWifiCredentials(body);
    }
};

void setupBleProvisioning() {
    BLEDevice::init(BLE_DEVICE_NAME);
    BLEServer* server = BLEDevice::createServer();
    server->setCallbacks(new ProvisioningServerCallbacks());

    BLEService* service = server->createService(BLE_SERVICE_UUID);

    BLECharacteristic* credentialsCharacteristic = service->createCharacteristic(
        BLE_WIFI_CREDENTIALS_UUID,
        BLECharacteristic::PROPERTY_WRITE
    );
    credentialsCharacteristic->setCallbacks(new WifiCredentialsCallbacks());

    statusCharacteristic = service->createCharacteristic(
        BLE_STATUS_UUID,
        BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
    );
    statusCharacteristic->addDescriptor(new BLE2902());

    service->start();

    BLEAdvertising* advertising = BLEDevice::getAdvertising();
    advertising->addServiceUUID(BLE_SERVICE_UUID);
    advertising->setScanResponse(true);
    advertising->setMinPreferred(0x06);
    advertising->setMaxPreferred(0x12);
    BLEDevice::startAdvertising();

    notifyStatus("idle", "", "waiting for Wi-Fi credentials");
    Serial.println("BLE provisioning is advertising");
}

void handleWifiReconnect() {
    const bool connected = WiFi.status() == WL_CONNECTED;
    if (connected) {
        if (!wifiConnectedState) {
            markWifiConnected(savedUdpPort, "Wi-Fi reconnected");
        }
        return;
    }

    if (wifiConnectedState) {
        wifiConnectedState = false;
        stopNetworkListeners();
        resetWifiReconnectBackoff();
        nextWifiReconnectAt = millis();
        notifyStatus("connecting", "", "Wi-Fi lost");
        Serial.println("Wi-Fi connection lost; reconnect scheduled");
    }

    if (!hasSavedWifiCredentials) {
        return;
    }

    const uint32_t now = millis();
    if (nextWifiReconnectAt == 0) {
        scheduleNextWifiReconnect(now);
        return;
    }

    if (hasReachedTime(now, nextWifiReconnectAt)) {
        beginWifiReconnectAttempt(now);
    }
}
}

void setup() {
    Serial.begin(115200);
    delay(500);

    loadDisplaySettings();
    setupDisplay();
    setupBleProvisioning();

    String ssid;
    String password;
    uint16_t udpPort = DEFAULT_UDP_PORT;
    if (loadWifiCredentials(ssid, password, udpPort)) {
        rememberWifiCredentials(ssid, password, udpPort);
        connectWifi(ssid, password, udpPort);
    }
}

void loop() {
    if (hasPendingWifiCredentials) {
        hasPendingWifiCredentials = false;
        const String ssid = pendingSsid;
        const String password = pendingPassword;
        const uint16_t udpPort = pendingUdpPort;
        rememberWifiCredentials(ssid, password, udpPort);
        if (connectWifi(ssid, password, udpPort)) {
            saveWifiCredentials(ssid, password, udpPort);
        }
    }

    handleWifiReconnect();
    handleDiscoveryPackets();
    sendPeriodicDiscoveryBeacon();
    handleUdpPackets();
    handleBridgePacketTimeout();
    handleStatusAnimation();
}
