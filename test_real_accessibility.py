#!/usr/bin/env python3
"""
Реальная проверка доступности сайтов
Проверяет не только TCP соединение, но и HTTP ответ
"""

import socket
import ssl
import urllib.request
import urllib.error
import sys
import time

def test_real_accessibility(hostname: str, port: int = 443, timeout: int = 10) -> dict:
    """Реальная проверка доступности сайта"""
    result = {
        "hostname": hostname,
        "port": port,
        "tcp_connected": False,
        "ssl_handshake": False,
        "http_response": False,
        "status_code": None,
        "error": None,
        "accessible": False
    }
    
    print(f"   🔍 Проверяю {hostname}:{port}...")
    
    # 1. TCP соединение
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        tcp_result = sock.connect_ex((hostname, port))
        if tcp_result == 0:
            result["tcp_connected"] = True
            print(f"      ✅ TCP соединение установлено")
        else:
            result["error"] = f"TCP connection failed: {tcp_result}"
            print(f"      ❌ TCP соединение не удалось: {tcp_result}")
            sock.close()
            return result
            
    except Exception as e:
        result["error"] = f"TCP error: {e}"
        print(f"      ❌ TCP ошибка: {e}")
        return result
    
    # 2. SSL handshake
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        ssl_sock = context.wrap_socket(sock, server_hostname=hostname, timeout=timeout)
        result["ssl_handshake"] = True
        print(f"      ✅ SSL handshake успешен")
        
    except Exception as e:
        result["error"] = f"SSL error: {e}"
        print(f"      ❌ SSL ошибка: {e}")
        try:
            sock.close()
        except:
            pass
        return result
    
    # 3. HTTP запрос и ответ
    try:
        http_request = f"GET / HTTP/1.1\r\nHost: {hostname}\r\nUser-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36\r\nConnection: close\r\n\r\n"
        
        ssl_sock.send(http_request.encode())
        response = ssl_sock.recv(8192)
        
        if response:
            response_str = response.decode('utf-8', errors='ignore')
            
            # Проверяем HTTP статус
            if "HTTP/" in response_str:
                result["http_response"] = True
                
                # Извлекаем статус код
                lines = response_str.split('\n')
                if lines:
                    status_line = lines[0]
                    if "200" in status_line:
                        result["status_code"] = 200
                        result["accessible"] = True
                        print(f"      ✅ HTTP 200 OK - сайт доступен")
                    elif "301" in status_line or "302" in status_line:
                        result["status_code"] = 301
                        result["accessible"] = True
                        print(f"      ✅ HTTP {status_line.split()[1]} - редирект, сайт доступен")
                    else:
                        result["status_code"] = status_line.split()[1] if len(status_line.split()) > 1 else "unknown"
                        print(f"      ⚠️ HTTP {result['status_code']} - сайт отвечает, но не нормально")
                else:
                    result["error"] = "No HTTP response lines"
                    print(f"      ❌ Нет HTTP ответа")
            else:
                result["error"] = "No HTTP response"
                print(f"      ❌ Нет HTTP ответа")
        else:
            result["error"] = "Empty response"
            print(f"      ❌ Пустой ответ")
            
    except Exception as e:
        result["error"] = f"HTTP error: {e}"
        print(f"      ❌ HTTP ошибка: {e}")
    
    finally:
        try:
            ssl_sock.close()
        except:
            pass
    
    return result

def test_with_urllib(hostname: str) -> dict:
    """Проверка через urllib (дополнительный метод)"""
    result = {
        "hostname": hostname,
        "accessible": False,
        "status_code": None,
        "error": None
    }
    
    try:
        url = f"https://{hostname}"
        request = urllib.request.Request(url)
        request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        with urllib.request.urlopen(request, timeout=10) as response:
            result["accessible"] = True
            result["status_code"] = response.getcode()
            print(f"      ✅ urllib: HTTP {result['status_code']} - доступен")
            
    except urllib.error.HTTPError as e:
        result["status_code"] = e.code
        if e.code in [200, 301, 302]:
            result["accessible"] = True
            print(f"      ✅ urllib: HTTP {e.code} - доступен")
        else:
            result["error"] = f"HTTP {e.code}"
            print(f"      ❌ urllib: HTTP {e.code}")
    except Exception as e:
        result["error"] = str(e)
        print(f"      ❌ urllib ошибка: {e}")
    
    return result

def main():
    """Основная функция"""
    print("🔍 РЕАЛЬНАЯ ПРОВЕРКА ДОСТУПНОСТИ САЙТОВ")
    print("=" * 50)
    
    # Список сайтов для проверки
    sites = [
        "www.youtube.com",
        "m.youtube.com", 
        "youtube.com",
        "google.com",
        "yandex.ru",
        "rutube.ru"
    ]
    
    # Добавляем сайты из аргументов
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg not in sites:
                sites.append(arg)
    
    results = {}
    
    for site in sites:
        print(f"\n🌐 Проверка {site}:")
        print("-" * 30)
        
        # 1. Прямая проверка
        result = test_real_accessibility(site)
        results[site] = result
        
        # 2. Дополнительная проверка через urllib
        if not result["accessible"]:
            print(f"   🔄 Дополнительная проверка через urllib...")
            urllib_result = test_with_urllib(site)
            if urllib_result["accessible"]:
                results[site]["accessible"] = True
                results[site]["urllib_accessible"] = True
        
        # Итог по сайту
        if results[site]["accessible"]:
            print(f"   🎯 ИТОГ: {site} - ✅ ДОСТУПЕН")
        else:
            print(f"   🎯 ИТОГ: {site} - ❌ НЕДОСТУПЕН")
            if results[site].get("error"):
                print(f"      Ошибка: {results[site]['error']}")
    
    # Общая статистика
    print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
    print("=" * 30)
    
    accessible_count = sum(1 for r in results.values() if r["accessible"])
    total_count = len(results)
    
    print(f"   📊 Всего проверено: {total_count}")
    print(f"   ✅ Доступно: {accessible_count}")
    print(f"   ❌ Недоступно: {total_count - accessible_count}")
    
    print(f"\n📋 Детальные результаты:")
    for site, result in results.items():
        status = "✅" if result["accessible"] else "❌"
        print(f"   {status} {site}")
        
        if result.get("tcp_connected"):
            print(f"      🟢 TCP: OK")
        if result.get("ssl_handshake"):
            print(f"      🔒 SSL: OK")
        if result.get("http_response"):
            print(f"      🌐 HTTP: OK (код {result.get('status_code', 'N/A')})")
        if result.get("error"):
            print(f"      ❌ Ошибка: {result['error']}")
    
    return results

if __name__ == "__main__":
    main()
