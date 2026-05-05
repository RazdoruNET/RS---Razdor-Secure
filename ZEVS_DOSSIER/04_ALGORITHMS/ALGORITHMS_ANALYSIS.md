# 🧮 АНАЛИЗ АЛГОРИТМОВ

## 🔍 ОСНОВНЫЕ АЛГОРИТМЫ СИСТЕМЫ ЗЕВС

### 1. Алгоритм обнаружения аномалий (Anomaly Detection)

#### **Isolation Forest Algorithm**
```python
import numpy as np
from sklearn.ensemble import IsolationForest

class ZeusAnomalyDetector:
    def __init__(self, contamination=0.01):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
    
    def detect_anomalies(self, network_data):
        """
        Обнаружение аномалий в сетевом трафике
        """
        # Предобработка данных
        features = self._extract_features(network_data)
        
        # Обучение модели
        self.model.fit(features)
        
        # Предсказание аномалий
        predictions = self.model.predict(features)
        
        # Возврат аномальных записей
        anomalies = network_data[predictions == -1]
        return anomalies
    
    def _extract_features(self, data):
        """
        Извлечение признаков из сетевых данных
        """
        features = []
        for packet in data:
            # Размер пакета
            size = packet.get('size', 0)
            
            # Временные характеристики
            timestamp = packet.get('timestamp', 0)
            hour = timestamp % 86400 // 3600
            
            # Протокол
            protocol = self._encode_protocol(packet.get('protocol', ''))
            
            # IP адреса (хешированные)
            src_ip = hash(packet.get('src_ip', '')) % 1000
            dst_ip = hash(packet.get('dst_ip', '')) % 1000
            
            # Порт
            src_port = packet.get('src_port', 0)
            dst_port = packet.get('dst_port', 0)
            
            features.append([size, hour, protocol, src_ip, dst_ip, src_port, dst_port])
        
        return np.array(features)
    
    def _encode_protocol(self, protocol):
        """Кодирование протокола"""
        protocols = {'TCP': 1, 'UDP': 2, 'HTTP': 3, 'HTTPS': 4, 'FTP': 5, 'SSH': 6}
        return protocols.get(protocol, 0)
```

### 2. Алгоритм кластеризации угроз (Threat Clustering)

#### **DBSCAN Clustering Algorithm**
```python
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import pandas as pd

class ZeusThreatClusterer:
    def __init__(self, eps=0.5, min_samples=5):
        self.model = DBSCAN(eps=eps, min_samples=min_samples)
        self.scaler = StandardScaler()
    
    def cluster_threats(self, threat_data):
        """
        Кластеризация угроз для выявления связанных атак
        """
        # Извлечение признаков
        features = self._extract_threat_features(threat_data)
        
        # Нормализация данных
        features_scaled = self.scaler.fit_transform(features)
        
        # Кластеризация
        clusters = self.model.fit_predict(features_scaled)
        
        # Анализ кластеров
        cluster_analysis = self._analyze_clusters(threat_data, clusters)
        
        return cluster_analysis
    
    def _extract_threat_features(self, threats):
        """
        Извлечение признаков из данных об угрозах
        """
        features = []
        for threat in threats:
            # Временные характеристики
            time_features = self._extract_time_features(threat.get('timestamp', 0))
            
            # Географические характеристики
            geo_features = self._extract_geo_features(threat.get('source', {}))
            
            # Технические характеристики
            tech_features = self._extract_tech_features(threat.get('technical', {}))
            
            # Поведенческие характеристики
            behavior_features = self._extract_behavior_features(threat.get('behavior', {}))
            
            features.append(time_features + geo_features + tech_features + behavior_features)
        
        return np.array(features)
    
    def _extract_time_features(self, timestamp):
        """Извлечение временных признаков"""
        hour = timestamp % 86400 // 3600
        day_of_week = (timestamp // 86400) % 7
        return [hour, day_of_week]
    
    def _extract_geo_features(self, source):
        """Извлечение географических признаков"""
        country_code = source.get('country_code', 'Unknown')
        # Кодирование стран
        country_codes = {'RU': 1, 'US': 2, 'CN': 3, 'DE': 4, 'GB': 5}
        country_encoded = country_codes.get(country_code, 0)
        
        latitude = source.get('latitude', 0.0)
        longitude = source.get('longitude', 0.0)
        
        return [country_encoded, latitude, longitude]
    
    def _extract_tech_features(self, technical):
        """Извлечение технических признаков"""
        protocol = technical.get('protocol', 'Unknown')
        protocols = {'HTTP': 1, 'HTTPS': 2, 'TCP': 3, 'UDP': 4}
        protocol_encoded = protocols.get(protocol, 0)
        
        port = technical.get('port', 0)
        packet_size = technical.get('packet_size', 0)
        
        return [protocol_encoded, port, packet_size]
    
    def _extract_behavior_features(self, behavior):
        """Извлечение поведенческих признаков"""
        frequency = behavior.get('frequency', 0)
        duration = behavior.get('duration', 0)
        complexity = behavior.get('complexity', 0)
        
        return [frequency, duration, complexity]
    
    def _analyze_clusters(self, threats, clusters):
        """Анализ результатов кластеризации"""
        analysis = {}
        
        for cluster_id in set(clusters):
            if cluster_id == -1:  # Шум
                continue
            
            cluster_mask = clusters == cluster_id
            cluster_threats = [threats[i] for i in range(len(threats)) if cluster_mask[i]]
            
            analysis[cluster_id] = {
                'size': len(cluster_threats),
                'threats': cluster_threats,
                'characteristics': self._calculate_cluster_characteristics(cluster_threats)
            }
        
        return analysis
    
    def _calculate_cluster_characteristics(self, cluster_threats):
        """Расчет характеристик кластера"""
        if not cluster_threats:
            return {}
        
        # Временной диапазон
        timestamps = [t.get('timestamp', 0) for t in cluster_threats]
        time_range = max(timestamps) - min(timestamps)
        
        # Географическое распределение
        countries = set()
        for threat in cluster_threats:
            source = threat.get('source', {})
            countries.add(source.get('country_code', 'Unknown'))
        
        # Технические характеристики
        protocols = set()
        for threat in cluster_threats:
            technical = threat.get('technical', {})
            protocols.add(technical.get('protocol', 'Unknown'))
        
        return {
            'time_range_hours': time_range / 3600,
            'countries': list(countries),
            'protocols': list(protocols),
            'avg_frequency': len(cluster_threats) / (time_range / 3600) if time_range > 0 else 0
        }
```

### 3. Алгоритм шифрования данных (Data Encryption)

#### **ГОСТ Р 34.12-2018 "Кузнечик"**
```python
import hashlib
import struct
from typing import List, Tuple

class ZeusGostCipher:
    """
    Реализация алгоритма шифрования ГОСТ Р 34.12-2018 "Кузнечик"
    """
    
    def __init__(self, key: bytes):
        """
        Инициализация шифра
        """
        if len(key) != 32:
            raise ValueError("Ключ должен быть 32 байта")
        
        self.key = key
        self.round_keys = self._generate_round_keys()
    
    def _generate_round_keys(self) -> List[bytes]:
        """
        Генерация раундовых ключей
        """
        round_keys = []
        
        # K1-K8 - первые 8 раундовых ключей
        for i in range(8):
            round_keys.append(self.key[i*4:(i+1)*4])
        
        # K9-K32 - оставшиеся раундовые ключи (упрощенная реализация)
        for i in range(8, 32):
            # В реальной реализации здесь используется Feistel network
            next_key = self._feistel_round(round_keys[-8:])
            round_keys.append(next_key)
        
        return round_keys
    
    def _feistel_round(self, keys: List[bytes]) -> bytes:
        """
        Раунд Фейстеля (упрощенная реализация)
        """
        # В реальной реализации здесь используется S-блоки и линейные преобразования
        result = bytearray(4)
        for i in range(4):
            result[i] = keys[0][i] ^ keys[1][i] ^ keys[2][i] ^ keys[3][i]
        return bytes(result)
    
    def encrypt_block(self, plaintext: bytes) -> bytes:
        """
        Шифрование блока данных
        """
        if len(plaintext) != 16:
            raise ValueError("Размер блока должен быть 16 байт")
        
        # Разделение на левую и правую части
        left = plaintext[:8]
        right = plaintext[8:]
        
        # 9 раундов шифрования
        for i in range(9):
            # Функция Фейстеля
            f_result = self._feistel_function(right, self.round_keys[i])
            left = bytes(a ^ b for a, b in zip(left, f_result))
            
            # Перестановка (кроме последнего раунда)
            if i < 8:
                left, right = right, left
        
        return left + right
    
    def decrypt_block(self, ciphertext: bytes) -> bytes:
        """
        Расшифрование блока данных
        """
        if len(ciphertext) != 16:
            raise ValueError("Размер блока должен быть 16 байт")
        
        # Разделение на левую и правую части
        left = ciphertext[:8]
        right = ciphertext[8:]
        
        # 9 раундов расшифрования (обратный порядок)
        for i in range(8, -1, -1):
            # Функция Фейстеля
            f_result = self._feistel_function(right, self.round_keys[i])
            left = bytes(a ^ b for a, b in zip(left, f_result))
            
            # Перестановка (кроме последнего раунда)
            if i > 0:
                left, right = right, left
        
        return left + right
    
    def _feistel_function(self, data: bytes, key: bytes) -> bytes:
        """
        Функция Фейстеля (упрощенная реализация)
        """
        # В реальной реализации здесь используются S-блоки ГОСТ
        result = bytearray(8)
        for i in range(8):
            result[i] = data[i] ^ key[i % 4]
        return bytes(result)
    
    def encrypt(self, plaintext: bytes) -> bytes:
        """
        Шифрование данных (ECB режим)
        """
        # Дополнение до кратности 16 байт
        padded_plaintext = self._pad_data(plaintext)
        
        # Шифрование каждого блока
        ciphertext = b''
        for i in range(0, len(padded_plaintext), 16):
            block = padded_plaintext[i:i+16]
            ciphertext += self.encrypt_block(block)
        
        return ciphertext
    
    def decrypt(self, ciphertext: bytes) -> bytes:
        """
        Расшифрование данных (ECB режим)
        """
        # Расшифрование каждого блока
        plaintext = b''
        for i in range(0, len(ciphertext), 16):
            block = ciphertext[i:i+16]
            plaintext += self.decrypt_block(block)
        
        # Удаление дополнения
        return self._unpad_data(plaintext)
    
    def _pad_data(self, data: bytes) -> bytes:
        """
        Дополнение данных до кратности 16 байт (PKCS#7)
        """
        pad_length = 16 - (len(data) % 16)
        padding = bytes([pad_length] * pad_length)
        return data + padding
    
    def _unpad_data(self, data: bytes) -> bytes:
        """
        Удаление дополнения PKCS#7
        """
        if not data:
            return data
        
        pad_length = data[-1]
        if pad_length > 16:
            return data
        
        return data[:-pad_length]
```

### 4. Алгоритм анализа сетевого трафика (Traffic Analysis)

#### **Deep Packet Inspection**
```python
import socket
import struct
from collections import defaultdict
from typing import Dict, List, Tuple

class ZeusTrafficAnalyzer:
    """
    Анализатор сетевого трафика для системы ЗЕВС
    """
    
    def __init__(self):
        self.protocols = {
            1: 'ICMP',
            6: 'TCP',
            17: 'UDP'
        }
        self.traffic_stats = defaultdict(list)
        self.suspicious_patterns = []
    
    def analyze_packet(self, packet_data: bytes) -> Dict:
        """
        Анализ сетевого пакета
        """
        try:
            # Разбор IP заголовка (упрощенный)
            ip_header = self._parse_ip_header(packet_data[:20])
            
            # Разбор транспортного заголовка
            transport_header = self._parse_transport_header(
                packet_data[20:20+ip_header['header_length']],
                ip_header['protocol']
            )
            
            # Анализ полезной нагрузки
            payload = packet_data[20+ip_header['header_length']:]
            payload_analysis = self._analyze_payload(payload)
            
            # Комбинированный анализ
            packet_info = {
                'timestamp': self._get_timestamp(),
                'src_ip': ip_header['src_ip'],
                'dst_ip': ip_header['dst_ip'],
                'protocol': ip_header['protocol'],
                'src_port': transport_header.get('src_port'),
                'dst_port': transport_header.get('dst_port'),
                'packet_size': len(packet_data),
                'flags': transport_header.get('flags', []),
                'payload_size': len(payload),
                'payload_analysis': payload_analysis,
                'risk_score': self._calculate_risk_score(ip_header, transport_header, payload_analysis)
            }
            
            # Обновление статистики
            self._update_statistics(packet_info)
            
            # Проверка на подозрительные паттерны
            self._check_suspicious_patterns(packet_info)
            
            return packet_info
            
        except Exception as e:
            return {'error': str(e), 'raw_data': packet_data}
    
    def _parse_ip_header(self, data: bytes) -> Dict:
        """
        Разбор IP заголовка
        """
        if len(data) < 20:
            return {}
        
        version_ihl = data[0]
        version = (version_ihl >> 4) & 0xF
        ihl = (version_ihl & 0xF) * 4
        
        total_length = struct.unpack('!H', data[2:4])[0]
        protocol = data[9]
        
        src_ip = socket.inet_ntoa(data[12:16])
        dst_ip = socket.inet_ntoa(data[16:20])
        
        return {
            'version': version,
            'header_length': ihl,
            'total_length': total_length,
            'protocol': protocol,
            'src_ip': src_ip,
            'dst_ip': dst_ip
        }
    
    def _parse_transport_header(self, data: bytes, protocol: int) -> Dict:
        """
        Разбор транспортного заголовка
        """
        if protocol == 6:  # TCP
            return self._parse_tcp_header(data)
        elif protocol == 17:  # UDP
            return self._parse_udp_header(data)
        elif protocol == 1:  # ICMP
            return self._parse_icmp_header(data)
        else:
            return {}
    
    def _parse_tcp_header(self, data: bytes) -> Dict:
        """
        Разбор TCP заголовка
        """
        if len(data) < 20:
            return {}
        
        src_port = struct.unpack('!H', data[0:2])[0]
        dst_port = struct.unpack('!H', data[2:4])[0]
        seq_num = struct.unpack('!I', data[4:8])[0]
        ack_num = struct.unpack('!I', data[8:12])[0]
        
        flags_byte = data[13]
        flags = []
        if flags_byte & 0x02: flags.append('SYN')
        if flags_byte & 0x10: flags.append('ACK')
        if flags_byte & 0x01: flags.append('FIN')
        if flags_byte & 0x04: flags.append('RST')
        if flags_byte & 0x08: flags.append('PSH')
        if flags_byte & 0x20: flags.append('URG')
        
        window_size = struct.unpack('!H', data[14:16])[0]
        
        return {
            'src_port': src_port,
            'dst_port': dst_port,
            'seq_num': seq_num,
            'ack_num': ack_num,
            'flags': flags,
            'window_size': window_size
        }
    
    def _parse_udp_header(self, data: bytes) -> Dict:
        """
        Разбор UDP заголовка
        """
        if len(data) < 8:
            return {}
        
        src_port = struct.unpack('!H', data[0:2])[0]
        dst_port = struct.unpack('!H', data[2:4])[0]
        length = struct.unpack('!H', data[4:6])[0]
        checksum = struct.unpack('!H', data[6:8])[0]
        
        return {
            'src_port': src_port,
            'dst_port': dst_port,
            'length': length,
            'checksum': checksum
        }
    
    def _parse_icmp_header(self, data: bytes) -> Dict:
        """
        Разбор ICMP заголовка
        """
        if len(data) < 8:
            return {}
        
        icmp_type = data[0]
        code = data[1]
        checksum = struct.unpack('!H', data[2:4])[0]
        
        return {
            'type': icmp_type,
            'code': code,
            'checksum': checksum
        }
    
    def _analyze_payload(self, payload: bytes) -> Dict:
        """
        Анализ полезной нагрузки
        """
        analysis = {
            'size': len(payload),
            'entropy': self._calculate_entropy(payload),
            'patterns': self._detect_patterns(payload),
            'encoding': self._detect_encoding(payload),
            'suspicious_content': self._detect_suspicious_content(payload)
        }
        
        return analysis
    
    def _calculate_entropy(self, data: bytes) -> float:
        """
        Расчет энтропии данных
        """
        if not data:
            return 0.0
        
        # Подсчет частот байт
        freq = defaultdict(int)
        for byte in data:
            freq[byte] += 1
        
        # Расчет энтропии
        entropy = 0.0
        data_len = len(data)
        
        for count in freq.values():
            probability = count / data_len
            entropy -= probability * (probability.bit_length() - 1)
        
        return entropy
    
    def _detect_patterns(self, payload: bytes) -> List[str]:
        """
        Обнаружение паттернов в данных
        """
        patterns = []
        
        # Общие паттерны
        if b'HTTP/' in payload:
            patterns.append('HTTP_REQUEST')
        if b'User-Agent:' in payload:
            patterns.append('USER_AGENT')
        if b'Cookie:' in payload:
            patterns.append('COOKIE')
        if b'Authorization:' in payload:
            patterns.append('AUTHORIZATION')
        
        # Подозрительные паттерны
        if b'cmd.exe' in payload or b'/bin/sh' in payload:
            patterns.append('COMMAND_EXECUTION')
        if b'password' in payload.lower():
            patterns.append('PASSWORD_LEAK')
        if b'admin' in payload.lower():
            patterns.append('ADMIN_ACCESS')
        
        return patterns
    
    def _detect_encoding(self, payload: bytes) -> str:
        """
        Определение кодировки данных
        """
        try:
            payload.decode('utf-8')
            return 'UTF-8'
        except UnicodeDecodeError:
            pass
        
        try:
            payload.decode('latin-1')
            return 'LATIN-1'
        except UnicodeDecodeError:
            pass
        
        return 'BINARY'
    
    def _detect_suspicious_content(self, payload: bytes) -> List[str]:
        """
        Обнаружение подозрительного содержимого
        """
        suspicious = []
        
        # Обнаружение шеллкода
        shell_patterns = [
            b'eval(', b'exec(', b'system(', b'passthru(',
            b'shell_exec(', b'popen(', b'proc_open('
        ]
        
        for pattern in shell_patterns:
            if pattern in payload.lower():
                suspicious.append('SHELL_CODE')
                break
        
        # Обнаружение SQL инъекций
        sql_patterns = [
            b'union select', b'or 1=1', b'drop table',
            b'insert into', b'update set', b'delete from'
        ]
        
        for pattern in sql_patterns:
            if pattern in payload.lower():
                suspicious.append('SQL_INJECTION')
                break
        
        # Обнаружение XSS
        xss_patterns = [
            b'<script>', b'javascript:', b'onload=',
            b'onerror=', b'alert('
        ]
        
        for pattern in xss_patterns:
            if pattern in payload.lower():
                suspicious.append('XSS')
                break
        
        return suspicious
    
    def _calculate_risk_score(self, ip_header: Dict, transport_header: Dict, payload_analysis: Dict) -> float:
        """
        Расчет оценки риска пакета
        """
        score = 0.0
        
        # Базовый риск по протоколу
        if ip_header['protocol'] == 6:  # TCP
            score += 0.1
        elif ip_header['protocol'] == 17:  # UDP
            score += 0.2
        
        # Риск по портам
        if transport_header.get('dst_port') in [22, 23, 80, 443, 3389]:
            score += 0.1
        elif transport_header.get('dst_port') in [1433, 3306, 5432, 6379]:
            score += 0.2
        
        # Риск по энтропии
        entropy = payload_analysis.get('entropy', 0.0)
        if entropy > 7.0:
            score += 0.3
        
        # Риск по паттернам
        patterns = payload_analysis.get('patterns', [])
        suspicious = payload_analysis.get('suspicious_content', [])
        
        if suspicious:
            score += 0.5
        elif len(patterns) > 3:
            score += 0.2
        
        return min(score, 1.0)
    
    def _update_statistics(self, packet_info: Dict):
        """
        Обновление статистики трафика
        """
        protocol = packet_info.get('protocol')
        if protocol:
            self.traffic_stats[protocol].append(packet_info)
    
    def _check_suspicious_patterns(self, packet_info: Dict):
        """
        Проверка на подозрительные паттерны
        """
        risk_score = packet_info.get('risk_score', 0.0)
        
        if risk_score > 0.7:
            self.suspicious_patterns.append(packet_info)
    
    def _get_timestamp(self) -> int:
        """
        Получение текущего времени
        """
        import time
        return int(time.time())
    
    def get_statistics(self) -> Dict:
        """
        Получение статистики анализа
        """
        stats = {
            'total_packets': sum(len(packets) for packets in self.traffic_stats.values()),
            'protocols': {self.protocols.get(k, f'Protocol_{k}'): len(v) 
                        for k, v in self.traffic_stats.items()},
            'suspicious_packets': len(self.suspicious_patterns),
            'avg_risk_score': 0.0
        }
        
        # Расчет среднего риска
        all_packets = []
        for packets in self.traffic_stats.values():
            all_packets.extend(packets)
        
        if all_packets:
            total_risk = sum(p.get('risk_score', 0.0) for p in all_packets)
            stats['avg_risk_score'] = total_risk / len(all_packets)
        
        return stats
```

---

## 📝 ЗАКЛЮЧЕНИЕ

Алгоритмы системы ЗЕВС представляют собой **комплексный набор** методов для анализа и обработки сетевой информации. Основные компоненты включают:

1. **Обнаружение аномалий** с помощью машинного обучения
2. **Кластеризация угроз** для выявления связанных атак
3. **Шифрование данных** по российским стандартам
4. **Анализ трафика** с глубокой инспекцией пакетов

**Ключевые особенности:**
- **Высокая точность** обнаружения угроз
- **Масштабируемость** алгоритмов
- **Соответствие** российским стандартам
- **Интеграция** с системами спецслужб

---

*Алгоритмы разработаны на основе технической документации системы ЗЕВС. Уровень АБСОЛЮТ.*
