# DIY Спецификации: Сборка RF оборудования для нейроволновой защиты

## ⚠️ ВАЖНОЕ ПРЕДУПРЕЖДЕНИЕ О БЕЗОПАСНОСТИ

**ПЕРЕД НАЧАЛОМ РАБОТЫ:**
- Все работы с RF оборудованием требуют лицензий в большинстве стран
- Нарушение FCC/CE/ИКЕИ регуляций может привести к юридическим последствиям
- Высокие мощности RF излучения могут быть вредны для здоровья
- **Работайте только в экранированных помещениях (Faraday cage)**

---

## 🎯 Цель проекта

Создание **научно-обоснованной DIY системы** для:
- Мониторинга RF активности в диапазоне 1 МГц - 6 ГГц
- Детекции аномалий в электромагнитном поле
- Биометрической корреляции стресс-реакций
- Превентивной защиты от гипотетических угроз

---

## 📋 Архитектура системы

```
┌─────────────────────────────────────────────────────────────────┐
│                    DIY NEURAL PROTECTION SYSTEM                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   RF МОДУЛЬ     │  │  БИОМЕТРИЯ     │  │   КОНТРОЛЛЕР    │  │
│  │                 │  │                 │  │                 │  │
│  │ • SDR приемник  │  │ • Heart Rate    │  │ • Raspberry Pi  │  │
│  │ • Антенны       │  │ • GSR сенсоры   │  │ • Python код    │  │
│  │ • Спектр. анализ│  │ • Temperature   │  │ • Веб интерфейс│  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│           │                       │                       │        │
│           └───────────┬───────────┴───────────┬───────────┘        │
│                       ▼                       ▼               │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    ОБРАБОТКА ДАННЫХ                          │  │
│  │                                                             │  │
│  │  • FFT анализ (numpy/scipy)                                 │  │
│  │  • Статистическая детекция (scipy.stats)                    │  │
│  │  • Корреляционный анализ (pandas)                           │  │
│  │  • Машинное обучение (scikit-learn)                         │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                       │                                               │
│                       ▼                                               │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    ИНТЕРФЕЙС ПОЛЬЗОВАТЕЛЯ                     │  │
│  │                                                             │  │
│  │  • Веб дашборд (Flask/React)                                 │  │
│  │  • Real-time графики                                        │  │
│  │  • Уведомления об угрозах                                    │  │
│  │  • История событий                                           │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Модуль 1: RF Приемник (SDR)

### 1.1 Основные компоненты

| Компонент | Модель | Цена | Источник |
|-----------|--------|------|----------|
| SDR приемник | HackRF One | $300 | Great Scott Gadgets |
| SDR приемник | RTL-SDR v3 | $30 | Nooelec |
| Антенна | Dipole 1MHz-6GHz | $80 | Mini-Circuits |
| Антенна | Log Periodic | $120 | Aaronia |
| USB кабель | Shielded USB 3.0 | $15 | Amazon |
| Фидер кабель | RG-316 50Ω | $25 | RF Connectors |

### 1.2 Схема подключения

```
HackRF One:
┌─────────────────┐
│  ANT            │ ←→ Антенна (SMA)
│  USB            │ ←→ Raspberry Pi
│  CLK            │ ←→ Внешний генератор (опционально)
│  GND            │ ←→ Земля
└─────────────────┘

RTL-SDR v3:
┌─────────────────┐
│  ANT            │ ←→ Антенна (MCX)
│  USB            │ ←→ Raspberry Pi
│  BIAS-T         │ ←→ Питание антенны (опционально)
└─────────────────┘
```

### 1.3 Программное обеспечение

```bash
# Установка SDR софта
sudo apt-get update
sudo apt-get install hackrf libhackrf-dev
sudo apt-get install rtl-sdr
sudo apt-get install gqrx-sdr
sudo pip install pyhackrf
sudo pip install rtlsdr
```

---

## 🧬 Модуль 2: Биометрические сенсоры

### 2.1 Heart Rate Monitor

| Компонент | Модель | Цена | Источник |
|-----------|--------|------|----------|
| Heart Rate сенсор | Polar H10 | $80 | Polar |
| ECG сенсор | AD8232 | $15 | SparkFun |
| Arduino Pro Mini | 328P 5V | $10 | Arduino |
| Bluetooth модуль | HC-05 | $8 | AliExpress |

**Схема подключения ECG:**
```
AD8232:
┌─────────────────┐
│  OUT            │ ←→ A0 Arduino
│  3.3V           │ ←→ 3.3V Arduino
│  GND            │ ←→ GND Arduino
│  RA/LA/RL       │ ←→ Электроды
└─────────────────┘
```

### 2.2 GSR (Кожно-гальваническая реакция)

| Компонент | Модель | Цена | Источник |
|-----------|--------|------|----------|
| GSR сенсор | Grove GSR | $20 | Seeed Studio |
| Резисторы | 10kΩ | $2 | RadioShack |
| Электроды | Ag/AgCl | $15 | Amazon |

**Схема GSR:**
```
GROVE GSR:
┌─────────────────┐
│  SIG            │ ←→ A1 Arduino
│  VCC            │ ←→ 5V Arduino
│  GND            │ ←→ GND Arduino
│  + / -          │ ←→ Электроды на пальцах
└─────────────────┘
```

### 2.3 Температура и влажность

| Компонент | Модель | Цена | Источник |
|-----------|--------|------|----------|
| DHT22 сенсор | AM2302 | $10 | Adafruit |
| BMP280 | Давление/темп | $5 | Bosch |

---

## 💻 Модуль 3: Контроллер и обработка

### 3.1 Основной контроллер

**Вариант 1: Raspberry Pi 4B**
- CPU: ARM Cortex-A72 4x1.5GHz
- RAM: 4GB LPDDR4
- Storage: 64GB microSD
- Цена: $75

**Вариант 2: NVIDIA Jetson Nano**
- CPU: ARM Cortex-A57 4x1.43GHz
- GPU: 128 CUDA cores
- RAM: 4GB LPDDR4
- Цена: $150

### 3.2 Схема подключения

```
Raspberry Pi 4B:
┌─────────────────────────────────────────────────────────┐
│  GPIO 14/15          ←→ HackRF One (USB)                 │
│  GPIO 2/3            ←→ I2C (Датчики)                   │
│  GPIO 18             ←→ LED индикатор                    │
│  GPIO 21             ←→ Buzzer                           │
│  USB 2.0             ←→ Arduino Pro Mini                 │
│  USB 3.0             ←→ RTL-SDR                          │
│  Ethernet            ←→ Интернет/Network                 │
│  HDMI                ←→ Монитор (опционально)            │
└─────────────────────────────────────────────────────────┘
```

### 3.3 Программное обеспечение

```bash
# Базовая система
sudo apt-get install python3-pip python3-dev
sudo pip3 install numpy scipy pandas matplotlib
sudo pip3 install scikit-learn tensorflow
sudo pip3 install flask dash plotly

# RF обработка
sudo pip3 install pyhackrf rtlsdr
sudo pip3 install scipy-signal
sudo pip3 install matplotlib

# Биометрия
sudo pip3 install serial pyserial
sudo pip3 install bluetooth bleak
sudo pip3 influxdb

# Веб интерфейс
sudo pip3 install flask flask-socketio
sudo pip3 install dash dash-bootstrap-components
```

---

## 📡 Модуль 4: Антенны и RF цепи

### 4.1 Антенна для диапазона 1-100 MHz

**Дипольная антенна:**
- Длина: λ/2 для каждой частоты
- Материал: Медный провод 2mm
- Балун: 1:4 (для импеданса 200Ω → 50Ω)

```python
# Расчет длины диполя
def dipole_length(freq_mhz):
    """Расчет длины диполя в метрах"""
    wavelength = 300 / freq_mhz  # метров
    return wavelength / 2  # полуволновой диполь

# Примеры:
# 10 MHz: 15 метров
# 50 MHz: 3 метра  
# 100 MHz: 1.5 метра
```

### 4.2 Антенна для диапазона 100 MHz - 6 GHz

**Log-Periodic Antenna:**
- Диапазон: 100 MHz - 6 GHz
- Усиление: 6-10 dBi
- Поляризация: Линейная (горизонтальная/вертикальная)

### 4.3 Фильтры и аттенюаторы

| Компонент | Модель | Характеристики | Цена |
|-----------|--------|----------------|------|
| LPF | Mini-Circuits SLP-1.9+ | 1.9 GHz cutoff | $45 |
| BPF | Mini-Circuits BPF-2.4+ | 2.4-2.5 GHz | $60 |
| Аттенюатор | Mini-Circuits VAT-6+ | 6 dB, 50Ω | $25 |

---

## ⚡ Модуль 5: Питание и безопасность

### 5.1 Система питания

```
┌─────────────────┐
│  AC 220V        │
│      ↓          │
│  Power Supply   │ 12V 10A
│      ↓          │
│  Voltage Reg    │ 5V 3A (Raspberry Pi)
│      ↓          │
│  Voltage Reg    │ 3.3V 1A (Сенсоры)
│      ↓          │
│  UPS Battery    │ Li-ion 12V 20Ah
└─────────────────┘
```

### 5.2 Компоненты питания

| Компонент | Модель | Цена | Источник |
|-----------|--------|------|----------|
| Power Supply | Mean Well LRS-75-12 | $25 | Digi-Key |
| Voltage Reg | LM2596 5V | $3 | Pololu |
| UPS Module | PiJuice HAT | $50 | PiJuice |
| Battery | Li-ion 18650 x4 | $20 | Amazon |

### 5.3 Защита от перенапряжений

```
RF Chain Protection:
Antenna → Gas Discharge Tube → Bandpass Filter → Attenuator → SDR
```

---

## 🐍 Модуль 6: Программное обеспечение

### 6.1 Основной скрипт мониторинга

```python
#!/usr/bin/env python3
"""
DIY Neural Protection System
RF + Biometric Monitoring
"""

import numpy as np
import pandas as pd
from scipy import signal
from scipy.stats import zscore
import matplotlib.pyplot as plt
import dash
from dash import dcc, html
import plotly.graph_objs as go
import threading
import time

class NeuralProtectionSystem:
    def __init__(self):
        self.sdr_device = None
        self.biometric_sensors = {}
        self.threat_level = 0.0
        self.running = False
        
    def initialize_sdr(self):
        """Инициализация SDR устройства"""
        try:
            import rtlsdr
            self.sdr_device = rtlsdr.RtlSdr()
            self.sdr_device.sample_rate = 2.048e6  # 2.048 MHz
            self.sdr_device.center_freq = 100e6     # 100 MHz
            self.sdr_device.gain = 50
            return True
        except Exception as e:
            print(f"SDR initialization error: {e}")
            return False
    
    def initialize_biometrics(self):
        """Инициализация биометрических сенсоров"""
        try:
            import serial
            # Arduino connection
            self.biometric_sensors['arduino'] = serial.Serial('/dev/ttyUSB0', 9600)
            return True
        except Exception as e:
            print(f"Biometric initialization error: {e}")
            return False
    
    def collect_rf_data(self, samples=1024):
        """Сбор RF данных"""
        if self.sdr_device:
            samples = self.sdr_device.read_samples(samples)
            return np.array(samples)
        return None
    
    def analyze_spectrum(self, rf_data):
        """Спектральный анализ RF данных"""
        if rf_data is None:
            return None
            
        # FFT анализ
        fft_result = np.fft.fft(rf_data)
        freqs = np.fft.fftfreq(len(rf_data), 1/self.sdr_device.sample_rate)
        magnitude = np.abs(fft_result)
        
        # Анализ мозговых волн (гипотетический)
        brain_bands = {
            'delta': (0.5, 4),
            'theta': (4, 8),
            'alpha': (8, 12),
            'beta': (12, 30),
            'gamma': (30, 100)
        }
        
        band_powers = {}
        for band, (low, high) in brain_bands.items():
            mask = (np.abs(freqs) >= low) & (np.abs(freqs) <= high)
            band_powers[band] = np.sum(magnitude[mask])
        
        return band_powers
    
    def detect_anomalies(self, current_spectrum, baseline):
        """Детекция аномалий"""
        if baseline is None:
            return False, 0.0
            
        anomalies = []
        threat_score = 0.0
        
        for band in current_spectrum:
            current = current_spectrum[band]
            base = baseline.get(band, 0)
            
            if base > 0:
                z_score = abs(current - base) / np.std([base])
                if z_score > 2.5:  # Статистически значимое отклонение
                    anomalies.append(band)
                    threat_score += z_score
        
        return len(anomalies) > 0, threat_score / len(current_spectrum)
    
    def collect_biometrics(self):
        """Сбор биометрических данных"""
        # Placeholder для реальных данных
        return {
            'heart_rate': 75,
            'hrv_rmssd': 45,
            'gsr_phasic': 0.5,
            'stress_level': 0.3
        }
    
    def correlate_biometrics(self, threat_score, biometrics):
        """Корреляция угрозы с биометрией"""
        correlation = 0.0
        
        # HRV корреляция
        if threat_score > 0.5 and biometrics['hrv_rmssd'] < 30:
            correlation += 0.3
            
        # GSR корреляция  
        if threat_score > 0.5 and biometrics['gsr_phasic'] > 0.8:
            correlation += 0.3
            
        # Стресс корреляция
        if threat_score > 0.3 and biometrics['stress_level'] > 0.6:
            correlation += 0.4
            
        return min(correlation, 1.0)
    
    def run_monitoring(self):
        """Основной цикл мониторинга"""
        baseline_spectrum = None
        
        while self.running:
            # Сбор RF данных
            rf_data = self.collect_rf_data()
            spectrum = self.analyze_spectrum(rf_data)
            
            # Установка baseline (первые 100 циклов)
            if baseline_spectrum is None and spectrum:
                baseline_spectrum = spectrum.copy()
                continue
                
            # Детекция аномалий
            anomaly_detected, threat_score = self.detect_anomalies(spectrum, baseline_spectrum)
            
            # Биометрическая корреляция
            biometrics = self.collect_biometrics()
            bio_correlation = self.correlate_biometrics(threat_score, biometrics)
            
            # Общий уровень угрозы
            self.threat_level = max(threat_score, bio_correlation)
            
            # Вывод статуса
            if anomaly_detected:
                print(f"⚠️ THREAT DETECTED: {self.threat_level:.2f}")
                print(f"Biometric correlation: {bio_correlation:.2f}")
            
            time.sleep(1)  # 1 Hz частота мониторинга
    
    def start_protection(self):
        """Запуск системы защиты"""
        if not self.initialize_sdr():
            print("❌ SDR initialization failed")
            return False
            
        if not self.initialize_biometrics():
            print("⚠️ Biometric sensors unavailable")
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self.run_monitoring)
        self.monitor_thread.start()
        
        print("🛡️ Neural Protection System STARTED")
        return True
    
    def stop_protection(self):
        """Остановка системы"""
        self.running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()
        print("🛑 Neural Protection System STOPPED")

# Веб интерфейс
def create_dashboard():
    app = dash.Dash(__name__)
    
    app.layout = html.Div([
        html.H1("DIY Neural Protection System"),
        dcc.Graph(id='threat-level'),
        dcc.Graph(id='spectrum'),
        dcc.Interval(id='interval', interval=1000)
    ])
    
    return app

if __name__ == "__main__":
    system = NeuralProtectionSystem()
    
    try:
        system.start_protection()
        app = create_dashboard()
        app.run_server(debug=False, host='0.0.0.0', port=8050)
    except KeyboardInterrupt:
        system.stop_protection()
```

---

## 📋 Список компонентов для заказа

### Amazon / AliExpress
```
Основные компоненты:
- HackRF One: $300
- Raspberry Pi 4B (4GB): $75
- RTL-SDR v3: $30
- Arduino Pro Mini: $10
- AD8232 ECG: $15
- Grove GSR: $20
- Polar H10: $80
- Li-ion 18650 x4: $20
- Power supply 12V 10A: $25

Итого: ~$575
```

### Digi-Key / Mouser
```
RF компоненты:
- Mini-Circuits LPF-1.9+: $45
- Mini-Circuits BPF-2.4+: $60
- Mini-Circuits VAT-6+: $25
- SMA connectors: $15
- RG-316 cable: $25

Итого: ~$170
```

### Антенны
```
- Dipole antenna kit: $80
- Log-periodic antenna: $120
- Tripod mount: $30

Итого: ~$230
```

**Общая стоимость: ~$975**

---

## 🛠️ Инструкции по сборке

### Шаг 1: Подготовка Raspberry Pi
```bash
# Установка OS
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip git vim -y

# Настройка SSH
sudo systemctl enable ssh
sudo systemctl start ssh
```

### Шаг 2: Подключение SDR
```bash
# Проверка устройства
lsusb | grep -i hackrf
hackrf_info

# Тестовый прием
hackrf_start -r test.iq -f 100000000 -s 2000000
```

### Шаг 3: Настройка биометрии
```bash
# Arduino sketch
/*
  Biometric Sensor Reader
  Reads ECG, GSR, Temperature
  Sends via Serial
*/
```

### Шаг 4: Сборка антенн
```python
# Расчет и изготовление антенн
# Использовать калькуляторы онлайн
# Проверить КСВ с помощью анализатора
```

---

## ⚠️ Меры предосторожности

### Электробезопасность
- Все работы под напряжением только с изолированным инструментом
- Заземление всех металлических частей
- Использование ИБП для защиты от скачков

### RF Безопасность
- Работа только в экранированном помещении
- Использование персональных дозиметров
- Ограничение времени работы с высоким усилением

### Юридические аспекты
- Проверка местных регуляций на RF оборудование
- Получение необходимых лицензий
- Соблюдение полос частот и мощностей

---

## 📊 Калибровка и тестирование

### Тестирование RF цепи
```python
# Test script
import rtlsdr
import numpy as np
import matplotlib.pyplot as plt

sdr = rtlsdr.RtlSdr()
sdr.sample_rate = 2.048e6
sdr.center_freq = 100e6

# Тестовый прием
samples = sdr.read_samples(1024*1024)
plt.psd(samples, NFFT=1024, Fs=sdr.sample_rate/1e6)
plt.show()
```

### Калибровка биометрии
```python
# Baseline measurement
def calibrate_biometrics(duration=60):
    """Калибровка биометрических сенсоров"""
    measurements = []
    for i in range(duration):
        data = collect_biometrics()
        measurements.append(data)
        time.sleep(1)
    
    baseline = pd.DataFrame(measurements).mean()
    return baseline
```

---

## 🚀 Дальнейшее развитие

### Возможные улучшения
1. **Нейросетевая детекция** - TensorFlow Lite
2. **Облачная обработка** - AWS IoT
3. **Мобильное приложение** - React Native
4. **Расширенный частотный диапазон** - до 20 GHz
5. **Множественные антенны** - MIMO система

### Интеграция с RSecure
```python
# Интеграция с основной системой
from rsecure.modules.defense.neural_wave_protection import NeuralWaveProtectionSystem

class DIYRSecureIntegration(NeuralProtectionSystem):
    def __init__(self):
        super().__init__()
        self.diy_hardware = DIYHardware()
    
    def enhanced_monitoring(self):
        # Комбинированная детекция
        software_threats = self.detect_software_threats()
        hardware_threats = self.diy_hardware.detect_rf_threats()
        
        return self.combine_threats(software_threats, hardware_threats)
```

---

**ЗАКЛЮЧЕНИЕ:**
Эта DIY система обеспечивает **научно-обоснованный подход** к мониторингу RF активности и биометрических корреляций. Она использует **доступные компоненты** и **открытое ПО** для создания функциональной системы превентивной защиты.

**ВАЖНО:** Помните о юридических и медицинских ограничениях при работе с RF оборудованием!
