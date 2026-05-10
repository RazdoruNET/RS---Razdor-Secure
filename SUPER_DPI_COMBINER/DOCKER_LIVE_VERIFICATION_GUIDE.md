# Docker Live Verification Guide

## ЭТАП 4 - Ручное тестирование Docker-капсуляции

### 🎯 Цель
Проверить работу DPI-Evading Transparent Proxy в Docker-контейнере с автоматизацией маршрутизации TPROXY.

### 📋 Предварительные требования

#### Системные требования
- **Linux хост** с правами sudo
- **Docker** и **docker-compose** установлены
- **iptables** и **iproute2** доступны
- **Сетевой интерфейс** с доступом в интернет

#### Проверка окружения
```bash
# Проверить Docker
docker --version
docker-compose --version

# Проверить права iptables
sudo iptables -L

# Проверить сетевые интерфейсы
ip addr show
```

### 🚀 Процедура тестирования

#### Шаг 1: Сборка и запуск контейнера
```bash
# Перейти в директорию проекта
cd /path/to/SUPER_DPI_COMBINER

# Создать директорию для логов
mkdir -p logs

# Собрать и запустить контейнер
sudo docker-compose up --build
```

**Ожидаемый результат:**
- Контейнер `dpi-evading-proxy` запущен
- В консоли Docker появляются логи настройки TPROXY
- iptables правила созданы для портов 80 и 443

#### Шаг 2: Проверка iptables правил
```bash
# В отдельном терминале на хосте
sudo iptables -t mangle -L OUTPUT -n -v
```

**Ожидаемый результат:**
```
Chain OUTPUT (policy ACCEPT)
target     prot opt source               destination         
TPROXY     tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:80 TPROXY mark 0x1/0x1 on-port:1080
TPROXY     tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:443 TPROXY mark 0x1/0x1 on-port:1080
DROP        udp  --  0.0.0.0/0            0.0.0.0/0            udp dpt:443
```

#### Шаг 3: Проверка маршрутизации
```bash
# Проверить ip rules
sudo ip rule list

# Проверить routing table
sudo ip route show table 100
```

**Ожидаемый результат:**
```
0:      from all lookup local 
32766:  from all lookup main 
32767:  from all lookup default 
100:     from all fwmark 0x1 lookup 100

local default dev lo table 100 
```

#### Шаг 4: Тестирование HTTP трафика
```bash
# В терминале хоста (вне Docker)
curl -v httpbin.org/get
```

**Ожидаемый результат:**
- HTTP запрос успешно выполняется
- В логах Docker видны сообщения о фрагментации
- Ответ от httpbin.org получен

#### Шаг 5: Wire-контроль с tcpdump
```bash
# В отдельном терминале хоста
sudo tcpdump -i <интерфейс> -vvv -X tcp port 80
```

**Ожидаемый результат:**
```
19:30:15.123456 IP 192.168.1.100.54321 > 93.184.216.34.80: Flags [P.], seq 1:30, win 64240, length 30
        0x0000:  4745 5420 2f68 7474 7062 696e 2e6f 7267  GET/httpbin.org
        0x0010:  2f67 6574 2048 5454 502f 312e 310d 0a48 6f73 743a /get HTTP/1.1 Host:
19:30:15.123456 IP 192.168.1.100.54321 > 93.184.216.34.80: Flags [P.], seq 31:60, win 64240, length 29
        0x0000:  2068 7462 696e 2e6f 7267 0d0a 5573 6572 2d41 httpbin.org User-A
        0x0010:  6765 6e74 3a20 6375 726c 2f37 2e32 302e 312e 310d 0a gent: curl/7.30.0.1
```

#### Шаг 6: Тестирование HTTPS трафика
```bash
# В терминале хоста
curl -v https://google.com
```

**Ожидаемый результат:**
- TLS handshake успешно выполняется через прокси
- Client Hello фрагментирован на чанки ≤30 байт
- SSL сертификат получен

#### Шаг 7: Проверка UDP блокировки
```bash
# Проверить что QUIC заблокирован
curl -v --http3 https://google.com
```

**Ожидаемый результат:**
- QUIC запросы блокируются
- Браузер автоматически переключается на TCP/HTTP2

### 🔄 Очистка и остановка

#### Остановка контейнера
```bash
# Нажать Ctrl+C в терминале с docker-compose
# Или выполнить:
sudo docker-compose down
```

#### Проверка очистки правил
```bash
# Проверить что iptables правила удалены
sudo iptables -t mangle -L OUTPUT -n

# Проверить что ip rules удалены
sudo ip rule list

# Проверить что routing table удалена
sudo ip route show table 100
```

**Ожидаемый результат:**
- Все TPROXY правила удалены
- Маршрутизация возвращена в исходное состояние
- Интернет работает напрямую

### 📊 Критерии успеха

#### ✅ Успешное тестирование
1. **Контейнер запускается** без ошибок
2. **iptables правила** созданы корректно
3. **HTTP трафик** перенаправляется через прокси
4. **Wire fragmentation** видна в tcpdump (чанки ≤30 байт)
5. **HTTPS трафик** работает с фрагментацией Client Hello
6. **UDP/443 блокируется** для принудительного TCP
7. **Очистка правил** работает корректно

#### ❌ Неуспешное тестирование
1. **Ошибки запуска** контейнера
2. **iptables ошибки** при создании правил
3. **Нет перенаправления** трафика
4. **Нет фрагментации** в tcpdump
5. **Ошибки очистки** при остановке

### 🔧 Диагностика проблем

#### Проблемы с правами доступа
```bash
# Проверить права Docker
sudo usermod -aG docker $USER
newgrp docker

# Или запускать с sudo
sudo docker-compose up --build
```

#### Проблемы с iptables
```bash
# Проверить модуль TPROXY
sudo modprobe xt_TPROXY
lsmod | grep TPROXY

# Проверить версию ядра
uname -r
# Требуется ядро 3.13+ для TPROXY
```

#### Проблемы с сетью
```bash
# Проверить сетевой интерфейс
ip link show

# Проверить маршрутизацию
ip route show

# Проверить что порт 1080 свободен
sudo netstat -tlnp | grep 1080
```

### 📋 Чек-лист для верификации

- [ ] Docker контейнер собран и запущен
- [ ] iptables правила созданы для портов 80 и 443
- [ ] UDP/443 заблокирован
- [ ] ip routing table 100 создана
- [ ] HTTP запросы проходят через прокси
- [ ] HTTPS запросы проходят через прокси
- [ ] Wire fragmentation видна в tcpdump
- [ ] Логи фрагментации видны в docker logs
- [ ] Очистка правил работает при остановке
- [ ] Интернет работает напрямую после очистки

### 🎯 Финальная верификация

После успешного выполнения всех шагов:
1. **DPI-Evading Transparent Proxy** работает в Docker-контейнере
2. **TPROXY маршрутизация** автоматически настраивается
3. **Wire fragmentation** подтверждена на packet level
4. **Zero-Fake Enforcement** соблюден (использован существующий код)
5. **Live Verification** пройдена успешно

**ЭТАП 4 ЗАВЕРШЕН** ✅
