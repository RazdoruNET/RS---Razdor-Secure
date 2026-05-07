# 💡 Примеры использования INFILTRATOR v2.0

<div align="center">

**Практические примеры и сценарии использования**

[![Examples](https://img.shields.io/badge/examples-complete-brightgreen.svg)](https://github.com/razdor/RS---Razdor-Secure)
[![Complexity](https://img.shields.io/badge/complexity-⭐⭐⭐-orange.svg)](docs/README.md)

</div>

## 📋 Содержание

- [Базовые примеры](#базовые-примеры)
- [Анализ различных типов кода](#анализ-различных-типов-кода)
- [Продвинутые сценарии](#продвинутые-сценарии)
- [Интеграционные примеры](#интеграционные-примеры)
- [Автоматизация](#автоматизация)
- [Кейсы из реальной практики](#кейсы-из-реальной-практики)

---

## 🚀 Базовые примеры

### Пример 1: Первый анализ

#### Создание тестового файла
```javascript
// simple_app.js
const axios = require('axios');

const config = {
    apiUrl: process.env.API_BASE_URL || 'https://api.example.com',
    timeout: parseInt(process.env.API_TIMEOUT || '5000')
};

const api = axios.create({
    baseURL: config.apiUrl,
    timeout: config.timeout,
    headers: {
        'Authorization': 'Bearer ' + process.env.API_KEY,
        'Content-Type': 'application/json'
    }
});

module.exports = {
    getUsers: () => api.get('/users'),
    createOrder: (data) => api.post('/orders', data),
    updateProfile: (id, data) => api.put(`/users/${id}`, data)
};
```

#### Анализ через командную строку
```bash
# Базовый анализ
python3 infiltrator_v2.py simple_app.js

# Расширенный анализ
python3 infiltrator_v2.py simple_app.js --stealth -o simple_results.json
```

#### Анализ через Python API
```python
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

# Конфигурация
config = InfiltratorConfig(enable_stealth=True)
infiltrator = InfiltratorV2(config)

# Анализ
results = infiltrator.analyze_bundle('simple_app.js')

# Вывод результатов
print(f"Found {len(results['endpoints'])} endpoints")
print(f"Risk level: {results['risk_assessment']['level']}")

for endpoint in results['endpoints']:
    print(f"- {endpoint['url']} ({endpoint['risk_level']})")
```

#### Ожидаемые результаты
```json
{
  "bundle_path": "simple_app.js",
  "bundle_size": 447,
  "endpoints": [
    {
      "call_target": "axios.get",
      "url": "/users",
      "risk_level": "MEDIUM",
      "tainted_source": "process.env"
    },
    {
      "call_target": "axios.post", 
      "url": "/orders",
      "risk_level": "MEDIUM",
      "tainted_source": "process.env"
    },
    {
      "call_target": "axios.put",
      "url": "/users/{id}",
      "risk_level": "MEDIUM",
      "tainted_source": "process.env"
    }
  ],
  "process_env_vars": ["API_BASE_URL", "API_TIMEOUT", "API_KEY"],
  "risk_assessment": {
    "level": "MEDIUM",
    "score": 15,
    "total_endpoints": 3
  }
}
```

---

### Пример 2: Анализ React приложения

#### React компонент
```javascript
// UserProfile.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const UserProfile = () => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        const fetchUser = async () => {
            try {
                const response = await axios.get(
                    `${process.env.REACT_APP_API_URL}/user/profile`,
                    {
                        headers: {
                            'Authorization': `Bearer ${localStorage.getItem('token')}`
                        }
                    }
                );
                setUser(response.data);
            } catch (error) {
                console.error('Failed to fetch user:', error);
            } finally {
                setLoading(false);
            }
        };
        
        fetchUser();
    }, []);
    
    const updateProfile = async (userData) => {
        try {
            await axios.put(
                `${process.env.REACT_APP_API_URL}/user/profile`,
                userData,
                {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        'Content-Type': 'application/json'
                    }
                }
            );
            // Обновление данных пользователя
            const response = await axios.get(
                `${process.env.REACT_APP_API_URL}/user/profile`
            );
            setUser(response.data);
        } catch (error) {
            console.error('Failed to update profile:', error);
        }
    };
    
    if (loading) return <div>Loading...</div>;
    
    return (
        <div>
            <h1>User Profile</h1>
            {/* Компонент UI */}
        </div>
    );
};

export default UserProfile;
```

#### Анализ
```python
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

# Конфигурация для React
config = InfiltratorConfig(
    enable_stealth=True,
    enable_source_map_recovery=True
)

infiltrator = InfiltratorV2(config)
results = infiltrator.analyze_bundle('UserProfile.js')

# Анализ результатов
react_endpoints = [ep for ep in results['endpoints'] if 'REACT_APP' in str(ep)]
print(f"Found {len(react_endpoints)} React endpoints")

for endpoint in react_endpoints:
    print(f"React endpoint: {endpoint['url']}")
    print(f"Risk: {endpoint['risk_level']}")
```

---

## 🔍 Анализ различных типов кода

### Пример 3: Обфусцированный код

#### Обфусцированный JavaScript
```javascript
// obfuscated_bundle.js
(function webpackUniversalModuleDefinition(root, factory) {
    if(typeof exports === 'object' && typeof module === 'object')
        module.exports = factory();
    else if(typeof define === 'function' && define.amd)
        define([], factory());
    else
        root["ApiClient"] = factory();
})(typeof self !== 'undefined' ? self : this, function() {
    
    // Обфусцированный строковый массив
    var _0x2a4b = [
        '\x68\x74\x74\x70\x73\x3a\x2f\x2f\x61\x70\x69\x2e\x65\x78\x61\x6d\x70\x6c\x65\x2e\x63\x6f\x6d',
        '\x2f\x61\x70\x69\x2f\x76\x31\x2f\x75\x73\x65\x72\x73',
        '\x2f\x61\x70\x69\x2f\x76\x31\x2f\x61\x75\x74\x68',
        '\x70\x72\x6f\x63\x65\x73\x73\x2e\x65\x6e\x76\x2e\x41\x50\x49\x5f\x4b\x45\x59'
    ];
    
    // Обфусцированные функции
    var _0x1f2c = function(_0x3e8d, _0x4b9a) {
        return axios['create']({
            'baseURL': _0x3e8d,
            'timeout': _0x4b9a,
            'headers': {
                'Authorization': 'Bearer ' + process['env'][_0x2a4b[3]]
            }
        });
    };
    
    var _0x5d7e = function(_0x6a1b) {
        return config['apiUrl'] + _0x6a1b;
    };
    
    var _0x7c9f = {
        getUsers: function() {
            return _0x1f2c(_0x5d7e(_0x2a4b[0]), 5000)['get'](_0x2a4b[1]);
        },
        authenticate: function(credentials) {
            return _0x1f2c(_0x5d7e(_0x2a4b[0]), 5000)['post'](_0x2a4b[2], credentials);
        }
    };
    
    return _0x7c9f;
});
```

#### Анализ обфусцированного кода
```python
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

# Конфигурация для обфусцированного кода
config = InfiltratorConfig(
    enable_stealth=True,  # Включить все методы деобфускации
    encryption_key=None,
    parallel_analysis=True
)

infiltrator = InfiltratorV2(config)
results = infiltrator.analyze_bundle('obfuscated_bundle.js')

# Анализ результатов
obfuscated_endpoints = [ep for ep in results['endpoints'] if ep.get('obfuscated')]
print(f"Found {len(obfuscated_endpoints)} obfuscated endpoints")

for endpoint in obfuscated_endpoints:
    print(f"⚠️  OBFUSCATED: {endpoint['url']}")
    print(f"   Risk: {endpoint['risk_level']}")
    print(f"   Instruction: {endpoint['instruction']}")

# Проверка переменных окружения
print(f"\nEnvironment variables found: {results['process_env_vars']}")
```

#### Результаты анализа
```json
{
  "endpoints": [
    {
      "call_target": "OBFUSCATED_API",
      "url": "https://api.example.com",
      "risk_level": "CRITICAL",
      "obfuscated": true,
      "instruction": "obfuscated_api_1_0@local = CALL(OBFUSCATED_API(https://api.example.com))"
    },
    {
      "call_target": "OBFUSCATED_API",
      "url": "/api/v1/users",
      "risk_level": "CRITICAL",
      "obfuscated": true
    },
    {
      "call_target": "OBFUSCATED_API",
      "url": "/api/v1/auth",
      "risk_level": "CRITICAL",
      "obfuscated": true
    }
  ],
  "process_env_vars": ["API_KEY"],
  "risk_assessment": {
    "level": "CRITICAL",
    "score": 40,
    "total_endpoints": 3
  }
}
```

---

### Пример 4: Vue.js приложение

#### Vue компонент
```javascript
// UserManagement.vue
<template>
  <div class="user-management">
    <h1>User Management</h1>
    <button @click="fetchUsers">Load Users</button>
    <button @click="createUser">Create User</button>
  </div>
</template>

<script>
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.VUE_APP_API_URL || 'http://localhost:3000',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.VUE_APP_API_KEY
  }
});

export default {
  name: 'UserManagement',
  data() {
    return {
      users: [],
      loading: false
    };
  },
  methods: {
    async fetchUsers() {
      this.loading = true;
      try {
        const response = await apiClient.get('/api/users');
        this.users = response.data;
      } catch (error) {
        console.error('Error fetching users:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async createUser(userData) {
      try {
        await apiClient.post('/api/users', userData);
        await this.fetchUsers(); // Обновить список
      } catch (error) {
        console.error('Error creating user:', error);
      }
    },
    
    async updateUser(userId, userData) {
      try {
        await apiClient.put(`/api/users/${userId}`, userData);
        await this.fetchUsers(); // Обновить список
      } catch (error) {
        console.error('Error updating user:', error);
      }
    },
    
    async deleteUser(userId) {
      try {
        await apiClient.delete(`/api/users/${userId}`);
        await this.fetchUsers(); // Обновить список
      } catch (error) {
        console.error('Error deleting user:', error);
      }
    }
  }
};
</script>
```

#### Анализ Vue.js
```python
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

# Анализ Vue компонента
config = InfiltratorConfig(enable_stealth=True)
infiltrator = InfiltratorV2(config)

results = infiltrator.analyze_bundle('UserManagement.vue')

# Фильтрация Vue специфичных эндпоинтов
vue_endpoints = []
for endpoint in results['endpoints']:
    if 'VUE_APP' in str(endpoint) or '/api/' in endpoint.get('url', ''):
        vue_endpoints.append(endpoint)

print(f"Vue.js endpoints found: {len(vue_endpoints)}")
for endpoint in vue_endpoints:
    print(f"- {endpoint['url']} ({endpoint['risk_level']})")
```

---

### Пример 5: Node.js backend

#### Express.js сервер
```javascript
// server.js
const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// Конфигурация
const config = {
    userServiceUrl: process.env.USER_SERVICE_URL || 'http://localhost:3001',
    orderServiceUrl: process.env.ORDER_SERVICE_URL || 'http://localhost:3002',
    paymentServiceUrl: process.env.PAYMENT_SERVICE_URL || 'http://localhost:3003',
    apiKey: process.env.API_KEY,
    databaseUrl: process.env.DATABASE_URL
};

// Middleware для проверки API ключа
const checkApiKey = (req, res, next) => {
    const key = req.headers['x-api-key'];
    if (key !== config.apiKey) {
        return res.status(401).json({ error: 'Invalid API key' });
    }
    next();
};

// Прокси для пользовательского сервиса
app.get('/api/users', async (req, res) => {
    try {
        const response = await axios.get(`${config.userServiceUrl}/users`, {
            headers: {
                'Authorization': `Bearer ${req.headers.authorization}`
            }
        });
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Создание заказа
app.post('/api/orders', checkApiKey, async (req, res) => {
    try {
        const orderData = req.body;
        
        // Проверка пользователя
        const userResponse = await axios.get(
            `${config.userServiceUrl}/users/${orderData.userId}`
        );
        
        if (!userResponse.data) {
            return res.status(404).json({ error: 'User not found' });
        }
        
        // Создание заказа
        const orderResponse = await axios.post(
            `${config.orderServiceUrl}/orders`,
            orderData
        );
        
        // Обработка платежа
        if (orderData.payment) {
            const paymentResponse = await axios.post(
                `${config.paymentServiceUrl}/payments`,
                {
                    orderId: orderResponse.data.id,
                    amount: orderData.amount,
                    currency: orderData.currency
                }
            );
            
            orderResponse.data.payment = paymentResponse.data;
        }
        
        res.json(orderResponse.data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Агрегация данных
app.get('/api/dashboard', checkApiKey, async (req, res) => {
    try {
        const [users, orders, payments] = await Promise.all([
            axios.get(`${config.userServiceUrl}/users/stats`),
            axios.get(`${config.orderServiceUrl}/orders/stats`),
            axios.get(`${config.paymentServiceUrl}/payments/stats`)
        ]);
        
        res.json({
            users: users.data,
            orders: orders.data,
            payments: payments.data
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
```

#### Анализ Node.js backend
```python
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

# Конфигурация для backend анализа
config = InfiltratorConfig(
    enable_stealth=True,
    parallel_analysis=True,
    max_workers=6
)

infiltrator = InfiltratorV2(config)
results = infiltrator.analyze_bundle('server.js')

# Анализ сервисных эндпоинтов
service_endpoints = []
for endpoint in results['endpoints']:
    url = endpoint.get('url', '')
    if any(service in url for service in ['USER_SERVICE', 'ORDER_SERVICE', 'PAYMENT_SERVICE']):
        service_endpoints.append(endpoint)

print(f"Service endpoints found: {len(service_endpoints)}")
for endpoint in service_endpoints:
    print(f"- {endpoint['url']} ({endpoint['risk_level']})")

# Анализ переменных окружения
env_vars = results['process_env_vars']
print(f"\nEnvironment variables: {len(env_vars)}")
for var in env_vars:
    print(f"- {var}")
```

---

## 🎯 Продвинутые сценарии

### Пример 6: Массовый анализ проекта

#### Скрипт для анализа всего проекта
```python
#!/usr/bin/env python3
"""
Массовый анализ JavaScript файлов в проекте
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

class ProjectAnalyzer:
    def __init__(self, config=None):
        self.config = config or InfiltratorConfig(
            enable_stealth=True,
            parallel_analysis=True,
            max_workers=4
        )
        self.infiltrator = InfiltratorV2(self.config)
        self.results = []
    
    def analyze_project(self, project_path, patterns=["*.js", "*.jsx", "*.ts", "*.tsx"]):
        """Анализ всего проекта"""
        project_path = Path(project_path)
        
        print(f"🔍 Analyzing project: {project_path}")
        
        # Поиск всех файлов
        files_to_analyze = []
        for pattern in patterns:
            files_to_analyze.extend(project_path.rglob(pattern))
        
        print(f"📁 Found {len(files_to_analyze)} files to analyze")
        
        # Анализ файлов
        for i, file_path in enumerate(files_to_analyze, 1):
            print(f"📄 [{i}/{len(files_to_analyze)}] Analyzing: {file_path.relative_to(project_path)}")
            
            try:
                result = self.infiltrator.analyze_bundle(str(file_path))
                result['file_path'] = str(file_path.relative_to(project_path))
                self.results.append(result)
                
                # Вывод краткой информации
                risk_level = result['risk_assessment']['level']
                endpoints_count = len(result['endpoints'])
                print(f"   ✓ Risk: {risk_level}, Endpoints: {endpoints_count}")
                
            except Exception as e:
                print(f"   ✗ Error: {e}")
                self.results.append({
                    'file_path': str(file_path.relative_to(project_path)),
                    'error': str(e)
                })
        
        return self.results
    
    def generate_report(self, output_path):
        """Генерация отчета"""
        if not self.results:
            print("❌ No results to report")
            return
        
        # Агрегация данных
        successful_results = [r for r in self.results if 'error' not in r]
        failed_results = [r for r in self.results if 'error' in r]
        
        total_files = len(self.results)
        successful_files = len(successful_results)
        failed_files = len(failed_results)
        
        # Статистика рисков
        risk_stats = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0
        }
        
        total_endpoints = 0
        all_env_vars = set()
        all_domains = set()
        
        for result in successful_results:
            risk_level = result['risk_assessment']['level']
            risk_stats[risk_level] += 1
            
            total_endpoints += len(result['endpoints'])
            all_env_vars.update(result['process_env_vars'])
            
            for endpoint in result['endpoints']:
                url = endpoint.get('url', '')
                if '://' in url:
                    domain = url.split('://')[1].split('/')[0]
                    all_domains.add(domain)
        
        # Создание отчета
        report = {
            'project_analysis': {
                'timestamp': datetime.now().isoformat(),
                'total_files': total_files,
                'successful_files': successful_files,
                'failed_files': failed_files,
                'success_rate': f"{(successful_files / total_files * 100):.1f}%" if total_files > 0 else "0%"
            },
            'risk_summary': risk_stats,
            'endpoint_summary': {
                'total_endpoints': total_endpoints,
                'avg_endpoints_per_file': total_endpoints / successful_files if successful_files > 0 else 0
            },
            'security_findings': {
                'total_env_vars': len(all_env_vars),
                'unique_domains': len(all_domains),
                'env_vars': list(all_env_vars),
                'domains': list(all_domains)
            },
            'detailed_results': self.results
        }
        
        # Сохранение отчета
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Вывод сводки
        self._print_summary(report)
        
        return report
    
    def _print_summary(self, report):
        """Вывод сводки анализа"""
        print("\n" + "="*60)
        print("📊 PROJECT ANALYSIS SUMMARY")
        print("="*60)
        
        analysis = report['project_analysis']
        print(f"📁 Files analyzed: {analysis['successful_files']}/{analysis['total_files']} ({analysis['success_rate']})")
        
        if analysis['failed_files'] > 0:
            print(f"❌ Failed files: {analysis['failed_files']}")
        
        print("\n🚨 RISK DISTRIBUTION:")
        risk_stats = report['risk_summary']
        for level, count in risk_stats.items():
            emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}[level]
            print(f"  {emoji} {level}: {count}")
        
        endpoints = report['endpoint_summary']
        print(f"\n🔗 ENDPOINTS:")
        print(f"  Total: {endpoints['total_endpoints']}")
        print(f"  Average per file: {endpoints['avg_endpoints_per_file']:.1f}")
        
        security = report['security_findings']
        print(f"\n🔒 SECURITY FINDINGS:")
        print(f"  Environment variables: {security['total_env_vars']}")
        print(f"  Unique domains: {security['unique_domains']}")
        
        if security['env_vars']:
            print(f"\n📋 Environment variables found:")
            for var in sorted(security['env_vars']):
                print(f"  - {var}")
        
        if security['domains']:
            print(f"\n🌐 External domains:")
            for domain in sorted(security['domains']):
                print(f"  - {domain}")
        
        print("="*60)

def main():
    parser = argparse.ArgumentParser(description='Mass project analysis')
    parser.add_argument('project_path', help='Path to project directory')
    parser.add_argument('-o', '--output', default='project_analysis.json', help='Output file')
    parser.add_argument('--patterns', nargs='+', default=['*.js', '*.jsx', '*.ts', '*.tsx'], help='File patterns')
    
    args = parser.parse_args()
    
    analyzer = ProjectAnalyzer()
    analyzer.analyze_project(args.project_path, args.patterns)
    analyzer.generate_report(args.output)
    
    print(f"\n📄 Report saved to: {args.output}")

if __name__ == "__main__":
    main()
```

#### Использование
```bash
# Анализ всего проекта
python3 project_analyzer.py /path/to/your/project -o security_report.json

# Анализ только JS файлов
python3 project_analyzer.py /path/to/project --patterns "*.js" -o js_report.json

# Анализ React проекта
python3 project_analyzer.py /path/to/react-app --patterns "*.js" "*.jsx" -o react_report.json
```

---

### Пример 7: Мониторинг безопасности в CI/CD

#### GitHub Actions workflow
```yaml
# .github/workflows/security-analysis.yml
name: Security Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * 1'  # Каждый понедельник в 2:00

jobs:
  security-analysis:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install Infiltrator
      run: |
        git clone https://github.com/razdor/RS---Razdor-Secure.git
        cd RS---Razdor-Secure/Infiltrator
        pip install -r requirements.txt
    
    - name: Run security analysis
      run: |
        cd RS---Razdor-Secure/Infiltrator
        python3 ../scripts/ci_analyzer.py \
          --project-path ${{ github.workspace }} \
          --output security_report.json \
          --fail-on-critical \
          --max-risk-score 50
    
    - name: Upload security report
      uses: actions/upload-artifact@v3
      with:
        name: security-report
        path: RS---Razdor-Secure/Infiltrator/security_report.json
        retention-days: 30
    
    - name: Comment PR with results
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const report = JSON.parse(fs.readFileSync('RS---Razdor-Secure/Infiltrator/security_report.json', 'utf8'));
          
          const comment = `
          ## 🔍 Security Analysis Results
          
          📊 **Summary:**
          - Files analyzed: ${report.project_analysis.successful_files}/${report.project_analysis.total_files}
          - Risk level: ${Object.entries(report.risk_summary).filter(([_, count]) => count > 0).map(([level, count]) => `${level}: ${count}`).join(', ')}
          - Total endpoints: ${report.endpoint_summary.total_endpoints}
          - Environment variables: ${report.security_findings.total_env_vars}
          
          🚨 **Critical Issues:** ${report.risk_summary.CRITICAL || 0}
          🔥 **High Risk Issues:** ${report.risk_summary.HIGH || 0}
          
          ${report.security_findings.env_vars.length > 0 ? `\n📋 **Environment Variables:**\n${report.security_findings.env_vars.map(v => `- \`${v}\``).join('\n')}` : ''}
          `;
          
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: comment
          });
```

#### CI анализатор
```python
#!/usr/bin/env python3
"""
CI/CD Security Analyzer
"""

import sys
import json
import argparse
from pathlib import Path
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

def main():
    parser = argparse.ArgumentParser(description='CI/CD Security Analysis')
    parser.add_argument('--project-path', required=True, help='Project path')
    parser.add_argument('--output', default='security_report.json', help='Output file')
    parser.add_argument('--fail-on-critical', action='store_true', help='Fail on critical issues')
    parser.add_argument('--max-risk-score', type=int, default=50, help='Maximum allowed risk score')
    parser.add_argument('--patterns', nargs='+', default=['*.js', '*.jsx', '*.ts', '*.tsx'], help='File patterns')
    
    args = parser.parse_args()
    
    # Конфигурация
    config = InfiltratorConfig(
        enable_stealth=True,
        parallel_analysis=True,
        max_workers=4
    )
    
    infiltrator = InfiltratorV2(config)
    
    # Анализ
    project_path = Path(args.project_path)
    results = []
    critical_issues = 0
    total_risk_score = 0
    
    print(f"🔍 Starting security analysis...")
    
    for pattern in args.patterns:
        for file_path in project_path.rglob(pattern):
            try:
                result = infiltrator.analyze_bundle(str(file_path))
                results.append(result)
                
                # Проверка критических проблем
                if result['risk_assessment']['level'] == 'CRITICAL':
                    critical_issues += 1
                    print(f"🔴 CRITICAL: {file_path.relative_to(project_path)}")
                
                total_risk_score += result['risk_assessment']['score']
                
                print(f"✓ {file_path.relative_to(project_path)} (Risk: {result['risk_assessment']['level']})")
                
            except Exception as e:
                print(f"✗ {file_path.relative_to(project_path)} - {e}")
    
    # Создание отчета
    report = {
        'project_analysis': {
            'total_files': len(results),
            'critical_issues': critical_issues,
            'total_risk_score': total_risk_score
        },
        'results': results
    }
    
    # Сохранение
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📊 Analysis Summary:")
    print(f"  Files analyzed: {len(results)}")
    print(f"  Critical issues: {critical_issues}")
    print(f"  Total risk score: {total_risk_score}")
    print(f"  Report saved to: {args.output}")
    
    # Проверка условий для выхода с ошибкой
    if args.fail_on_critical and critical_issues > 0:
        print(f"\n❌ Build failed: {critical_issues} critical issues found")
        sys.exit(1)
    
    if total_risk_score > args.max_risk_score:
        print(f"\n❌ Build failed: Risk score {total_risk_score} exceeds maximum {args.max_risk_score}")
        sys.exit(1)
    
    print(f"\n✅ Security check passed!")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

---

## 🔌 Интеграционные примеры

### Пример 8: Flask API сервис

#### Flask приложение
```python
# security_api.py
from flask import Flask, request, jsonify, send_file
import tempfile
import os
import json
from datetime import datetime
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# Конфигурация
ALLOWED_EXTENSIONS = {'js', 'jsx', 'ts', 'tsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/analyze', methods=['POST'])
def analyze_file():
    """Анализ загруженного файла"""
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    # Сохранение временного файла
    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.js', delete=False) as tmp_file:
        file.save(tmp_file.name)
        tmp_path = tmp_file.name
    
    try:
        # Получение опций из запроса
        enable_stealth = request.form.get('stealth', 'true').lower() == 'true'
        max_workers = int(request.form.get('workers', 4))
        
        # Конфигурация
        config = InfiltratorConfig(
            enable_stealth=enable_stealth,
            parallel_analysis=True,
            max_workers=max_workers
        )
        
        infiltrator = InfiltratorV2(config)
        results = infiltrator.analyze_bundle(tmp_path)
        
        # Добавление метаданных
        results['analysis_metadata'] = {
            'filename': file.filename,
            'file_size': os.path.getsize(tmp_path),
            'analysis_time': datetime.now().isoformat(),
            'config': {
                'stealth': enable_stealth,
                'workers': max_workers
            }
        }
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Очистка
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.route('/api/batch-analyze', methods=['POST'])
def batch_analyze():
    """Массовый анализ файлов"""
    
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files selected'}), 400
    
    results = []
    errors = []
    
    for file in files:
        if not allowed_file(file.filename):
            errors.append({'filename': file.filename, 'error': 'Invalid file type'})
            continue
        
        # Сохранение временного файла
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.js', delete=False) as tmp_file:
            file.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        try:
            config = InfiltratorConfig(enable_stealth=True)
            infiltrator = InfiltratorV2(config)
            result = infiltrator.analyze_bundle(tmp_path)
            
            result['filename'] = file.filename
            results.append(result)
            
        except Exception as e:
            errors.append({'filename': file.filename, 'error': str(e)})
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    return jsonify({
        'successful_analyses': results,
        'errors': errors,
        'summary': {
            'total_files': len(files),
            'successful': len(results),
            'failed': len(errors)
        }
    })

@app.route('/api/analyze-code', methods=['POST'])
def analyze_code():
    """Анализ кода из тела запроса"""
    
    data = request.get_json()
    if not data or 'code' not in data:
        return jsonify({'error': 'No code provided'}), 400
    
    code = data['code']
    enable_stealth = data.get('stealth', True)
    
    # Сохранение временного файла
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp_file:
        tmp_file.write(code)
        tmp_path = tmp_file.name
    
    try:
        config = InfiltratorConfig(enable_stealth=enable_stealth)
        infiltrator = InfiltratorV2(config)
        results = infiltrator.analyze_bundle(tmp_path)
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверка здоровья сервиса"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0'
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """Получение доступной конфигурации"""
    return jsonify({
        'max_file_size': app.config['MAX_CONTENT_LENGTH'],
        'allowed_extensions': list(ALLOWED_EXTENSIONS),
        'default_config': {
            'stealth': True,
            'workers': 4,
            'timeout': 300
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

#### Docker конфигурация
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание директории для временных файлов
RUN mkdir -p /tmp/uploads

# Экспорт порта
EXPOSE 5000

# Запуск
CMD ["python", "security_api.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  infiltrator-api:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./uploads:/tmp/uploads
    environment:
      - FLASK_ENV=production
    restart: unless-stopped
```

#### Использование API
```bash
# Анализ файла
curl -X POST -F "file=@app.js" http://localhost:5000/api/analyze

# Анализ с опциями
curl -X POST \
  -F "file=@app.js" \
  -F "stealth=true" \
  -F "workers=8" \
  http://localhost:5000/api/analyze

# Анализ кода
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"code": "axios.get(\"https://api.example.com/users\")"}' \
  http://localhost:5000/api/analyze-code

# Массовый анализ
curl -X POST \
  -F "files=@app1.js" \
  -F "files=@app2.js" \
  http://localhost:5000/api/batch-analyze
```

---

## 🤖 Автоматизация

### Пример 9: Ежедневный мониторинг

#### Скрипт мониторинга
```python
#!/usr/bin/env python3
"""
Ежедневный мониторинг безопасности
"""

import os
import json
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

class SecurityMonitor:
    def __init__(self, config_file='monitor_config.json'):
        self.config = self.load_config(config_file)
        self.infiltrator = InfiltratorV2(InfiltratorConfig(enable_stealth=True))
    
    def load_config(self, config_file):
        """Загрузка конфигурации"""
        default_config = {
            'projects': [],
            'email': {
                'enabled': False,
                'smtp_server': '',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_email': '',
                'to_emails': []
            },
            'thresholds': {
                'max_critical_issues': 0,
                'max_risk_score': 50,
                'max_new_endpoints': 10
            }
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def monitor_projects(self):
        """Мониторинг всех проектов"""
        all_results = []
        
        for project in self.config['projects']:
            print(f"🔍 Monitoring: {project['name']}")
            
            project_results = self.analyze_project(project)
            all_results.append({
                'project': project['name'],
                'path': project['path'],
                'results': project_results
            })
        
        # Генерация отчета
        report = self.generate_daily_report(all_results)
        
        # Отправка уведомлений
        if self.config['email']['enabled']:
            self.send_email_report(report)
        
        # Сохранение отчета
        self.save_report(report)
        
        return report
    
    def analyze_project(self, project):
        """Анализ одного проекта"""
        project_path = Path(project['path'])
        patterns = project.get('patterns', ['*.js', '*.jsx', '*.ts', '*.tsx'])
        
        results = []
        critical_issues = 0
        total_risk_score = 0
        
        for pattern in patterns:
            for file_path in project_path.rglob(pattern):
                try:
                    result = self.infiltrator.analyze_bundle(str(file_path))
                    results.append(result)
                    
                    if result['risk_assessment']['level'] == 'CRITICAL':
                        critical_issues += 1
                    
                    total_risk_score += result['risk_assessment']['score']
                    
                except Exception as e:
                    print(f"Error analyzing {file_path}: {e}")
        
        return {
            'files_analyzed': len(results),
            'critical_issues': critical_issues,
            'total_risk_score': total_risk_score,
            'results': results
        }
    
    def generate_daily_report(self, all_results):
        """Генерация ежедневного отчета"""
        total_files = sum(r['results']['files_analyzed'] for r in all_results)
        total_critical = sum(r['results']['critical_issues'] for r in all_results)
        total_risk_score = sum(r['results']['total_risk_score'] for r in all_results)
        
        report = {
            'date': datetime.now().isoformat(),
            'summary': {
                'projects_monitored': len(all_results),
                'total_files_analyzed': total_files,
                'total_critical_issues': total_critical,
                'total_risk_score': total_risk_score,
                'status': 'ALERT' if total_critical > 0 else 'OK'
            },
            'projects': all_results,
            'alerts': self.generate_alerts(all_results)
        }
        
        return report
    
    def generate_alerts(self, all_results):
        """Генерация алертов"""
        alerts = []
        thresholds = self.config['thresholds']
        
        for project_result in all_results:
            project_name = project_result['project']
            results = project_result['results']
            
            if results['critical_issues'] > thresholds['max_critical_issues']:
                alerts.append({
                    'type': 'CRITICAL_ISSUES',
                    'project': project_name,
                    'value': results['critical_issues'],
                    'threshold': thresholds['max_critical_issues']
                })
            
            if results['total_risk_score'] > thresholds['max_risk_score']:
                alerts.append({
                    'type': 'HIGH_RISK_SCORE',
                    'project': project_name,
                    'value': results['total_risk_score'],
                    'threshold': thresholds['max_risk_score']
                })
        
        return alerts
    
    def send_email_report(self, report):
        """Отправка email отчета"""
        if not self.config['email']['enabled']:
            return
        
        # Создание email
        msg = MimeMultipart()
        msg['From'] = self.config['email']['from_email']
        msg['To'] = ', '.join(self.config['email']['to_emails'])
        msg['Subject'] = f"Security Monitor Report - {report['date'][:10]}"
        
        # Текст письма
        body = self.generate_email_body(report)
        msg.attach(MimeText(body, 'html'))
        
        # Отправка
        try:
            with smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port']) as server:
                server.starttls()
                server.login(self.config['email']['username'], self.config['email']['password'])
                server.send_message(msg)
            
            print("📧 Email report sent")
        except Exception as e:
            print(f"Failed to send email: {e}")
    
    def generate_email_body(self, report):
        """Генерация тела email"""
        summary = report['summary']
        alerts = report['alerts']
        
        status_emoji = "🚨" if summary['status'] == 'ALERT' else "✅"
        
        body = f"""
        <h2>{status_emoji} Security Monitor Report</h2>
        <p><strong>Date:</strong> {report['date'][:10]}</p>
        
        <h3>📊 Summary</h3>
        <ul>
            <li>Projects monitored: {summary['projects_monitored']}</li>
            <li>Files analyzed: {summary['total_files_analyzed']}</li>
            <li>Critical issues: {summary['total_critical_issues']}</li>
            <li>Total risk score: {summary['total_risk_score']}</li>
            <li>Status: <strong>{summary['status']}</strong></li>
        </ul>
        """
        
        if alerts:
            body += "<h3>🚨 Alerts</h3><ul>"
            for alert in alerts:
                body += f"<li><strong>{alert['project']}</strong>: {alert['type']} - {alert['value']} (threshold: {alert['threshold']})</li>"
            body += "</ul>"
        
        body += "<h3>📋 Project Details</h3>"
        for project in report['projects']:
            body += f"""
            <h4>{project['project']}</h4>
            <ul>
                <li>Files analyzed: {project['results']['files_analyzed']}</li>
                <li>Critical issues: {project['results']['critical_issues']}</li>
                <li>Risk score: {project['results']['total_risk_score']}</li>
            </ul>
            """
        
        return body
    
    def save_report(self, report):
        """Сохранение отчета"""
        reports_dir = Path('security_reports')
        reports_dir.mkdir(exist_ok=True)
        
        filename = f"report_{report['date'][:10].replace('-', '')}.json"
        filepath = reports_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📄 Report saved: {filepath}")

def main():
    monitor = SecurityMonitor()
    report = monitor.monitor_projects()
    
    # Вывод в консоль
    print(f"\n📊 Monitor Summary:")
    print(f"  Projects: {report['summary']['projects_monitored']}")
    print(f"  Files: {report['summary']['total_files_analyzed']}")
    print(f"  Critical issues: {report['summary']['total_critical_issues']}")
    print(f"  Status: {report['summary']['status']}")

if __name__ == "__main__":
    main()
```

#### Конфигурация мониторинга
```json
{
  "projects": [
    {
      "name": "Frontend App",
      "path": "/path/to/frontend",
      "patterns": ["*.js", "*.jsx"]
    },
    {
      "name": "Backend API",
      "path": "/path/to/backend",
      "patterns": ["*.js"]
    }
  ],
  "email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "from_email": "security-monitor@company.com",
    "to_emails": ["security-team@company.com", "dev-team@company.com"]
  },
  "thresholds": {
    "max_critical_issues": 0,
    "max_risk_score": 50,
    "max_new_endpoints": 10
  }
}
```

---

## 🎯 Кейсы из реальной практики

### Пример 10: Аудит e-commerce приложения

#### Сценарий
Большой e-commerce сайт с React frontend и Node.js backend. Нужно найти все API эндпоинты и проверить безопасность.

#### Реализация
```python
#!/usr/bin/env python3
"""
Аудит e-commerce приложения
"""

from infiltrator_v2 import InfiltratorV2, InfiltratorConfig
import json
from pathlib import Path

class ECommerceAuditor:
    def __init__(self):
        self.config = InfiltratorConfig(
            enable_stealth=True,
            parallel_analysis=True,
            max_workers=6
        )
        self.infiltrator = InfiltratorV2(self.config)
    
    def audit_frontend(self, frontend_path):
        """Аудит frontend"""
        print("🔍 Auditing frontend...")
        
        frontend_results = {
            'components': [],
            'api_endpoints': [],
            'env_vars': set(),
            'security_issues': []
        }
        
        # Анализ React компонентов
        for js_file in Path(frontend_path).rglob("*.js*"):
            try:
                result = self.infiltrator.analyze_bundle(str(js_file))
                
                # Классификация результатов
                for endpoint in result['endpoints']:
                    if endpoint['risk_level'] in ['HIGH', 'CRITICAL']:
                        frontend_results['security_issues'].append({
                            'file': str(js_file),
                            'endpoint': endpoint
                        })
                    
                    frontend_results['api_endpoints'].append(endpoint)
                
                frontend_results['env_vars'].update(result['process_env_vars'])
                frontend_results['components'].append({
                    'file': str(js_file),
                    'endpoints_count': len(result['endpoints']),
                    'risk_level': result['risk_assessment']['level']
                })
                
            except Exception as e:
                print(f"Error analyzing {js_file}: {e}")
        
        frontend_results['env_vars'] = list(frontend_results['env_vars'])
        return frontend_results
    
    def audit_backend(self, backend_path):
        """Аудит backend"""
        print("🔍 Auditing backend...")
        
        backend_results = {
            'services': [],
            'external_apis': [],
            'env_vars': set(),
            'security_issues': []
        }
        
        for js_file in Path(backend_path).rglob("*.js"):
            try:
                result = self.infiltrator.analyze_bundle(str(js_file))
                
                # Поиск внешних API
                for endpoint in result['endpoints']:
                    url = endpoint.get('url', '')
                    if 'http' in url and not any(local in url for local in ['localhost', '127.0.0.1']):
                        backend_results['external_apis'].append(endpoint)
                    
                    if endpoint['risk_level'] in ['HIGH', 'CRITICAL']:
                        backend_results['security_issues'].append({
                            'file': str(js_file),
                            'endpoint': endpoint
                        })
                
                backend_results['env_vars'].update(result['process_env_vars'])
                backend_results['services'].append({
                    'file': str(js_file),
                    'endpoints_count': len(result['endpoints']),
                    'risk_level': result['risk_assessment']['level']
                })
                
            except Exception as e:
                print(f"Error analyzing {js_file}: {e}")
        
        backend_results['env_vars'] = list(backend_results['env_vars'])
        return backend_results
    
    def generate_audit_report(self, frontend_results, backend_results):
        """Генерация отчета аудита"""
        report = {
            'audit_summary': {
                'frontend_components': len(frontend_results['components']),
                'backend_services': len(backend_results['services']),
                'total_endpoints': len(frontend_results['api_endpoints']) + len(backend_results['external_apis']),
                'security_issues': len(frontend_results['security_issues']) + len(backend_results['security_issues']),
                'total_env_vars': len(set(frontend_results['env_vars'] + backend_results['env_vars']))
            },
            'frontend_audit': frontend_results,
            'backend_audit': backend_results,
            'recommendations': self.generate_recommendations(frontend_results, backend_results)
        }
        
        return report
    
    def generate_recommendations(self, frontend_results, backend_results):
        """Генерация рекомендаций"""
        recommendations = []
        
        # Проверка критических проблем
        all_issues = frontend_results['security_issues'] + backend_results['security_issues']
        if all_issues:
            recommendations.append({
                'priority': 'CRITICAL',
                'title': 'Critical Security Issues Found',
                'description': f'Found {len(all_issues)} critical security issues that require immediate attention.',
                'action': 'Review and fix all critical issues before production deployment'
            })
        
        # Проверка переменных окружения
        sensitive_vars = ['API_KEY', 'SECRET', 'PASSWORD', 'TOKEN']
        found_sensitive = [var for var in frontend_results['env_vars'] + backend_results['env_vars'] 
                          if any(sensitive in var for sensitive in sensitive_vars)]
        
        if found_sensitive:
            recommendations.append({
                'priority': 'HIGH',
                'title': 'Sensitive Environment Variables Detected',
                'description': f'Found sensitive variables: {", ".join(found_sensitive)}',
                'action': 'Ensure proper handling of sensitive environment variables'
            })
        
        # Проверка обфусцированного кода
        obfuscated_endpoints = [ep for ep in frontend_results['api_endpoints'] + backend_results['external_apis'] 
                               if ep.get('obfuscated')]
        
        if obfuscated_endpoints:
            recommendations.append({
                'priority': 'MEDIUM',
                'title': 'Obfuscated Code Detected',
                'description': f'Found {len(obfuscated_endpoints)} obfuscated endpoints',
                'action': 'Review obfuscated code for potential security risks'
            })
        
        return recommendations

def main():
    auditor = ECommerceAuditor()
    
    # Аудит
    frontend_results = auditor.audit_frontend('/path/to/frontend')
    backend_results = auditor.audit_backend('/path/to/backend')
    
    # Генерация отчета
    report = auditor.generate_audit_report(frontend_results, backend_results)
    
    # Сохранение
    with open('ecommerce_audit_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Вывод сводки
    summary = report['audit_summary']
    print(f"\n📊 E-Commerce Audit Summary:")
    print(f"  Frontend components: {summary['frontend_components']}")
    print(f"  Backend services: {summary['backend_services']}")
    print(f"  Total endpoints: {summary['total_endpoints']}")
    print(f"  Security issues: {summary['security_issues']}")
    print(f"  Environment variables: {summary['total_env_vars']}")
    
    print(f"\n📋 Recommendations:")
    for rec in report['recommendations']:
        print(f"  {rec['priority']}: {rec['title']}")

if __name__ == "__main__":
    main()
```

---

## 📚 Дополнительные ресурсы

### Пример 11: Обучающий набор данных

#### Генератор тестовых файлов
```python
#!/usr/bin/env python3
"""
Генератор тестовых JavaScript файлов для обучения
"""

import os
import json
from pathlib import Path

class TestDataGenerator:
    def __init__(self, output_dir='test_data'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_simple_api(self):
        """Генерация простого API файла"""
        content = '''
const axios = require('axios');

const api = {
    getUsers: () => axios.get(process.env.API_URL + '/users'),
    createUser: (data) => axios.post(process.env.API_URL + '/users', data),
    updateUser: (id, data) => axios.put(process.env.API_URL + '/users/' + id, data),
    deleteUser: (id) => axios.delete(process.env.API_URL + '/users/' + id)
};

module.exports = api;
'''
        
        with open(self.output_dir / 'simple_api.js', 'w') as f:
            f.write(content)
    
    def generate_obfuscated_api(self):
        """Генерация обфусцированного API"""
        content = '''
var _0x2a4b = ['\\x68\\x74\\x74\\x70\\x73://api.example.com', '\\x2f\\x61\\x70\\x69\\x2f\\x76\\x31'];
var _0x1f2c = function(_0x3e8d) { return axios['get'](_0x2a4b[0] + _0x3e8d); };
var _0x5d7e = function() { return _0x1f2c(_0x2a4b[1] + '/users'); };
'''
        
        with open(self.output_dir / 'obfuscated_api.js', 'w') as f:
            f.write(content)
    
    def generate_react_component(self):
        """Генерация React компонента"""
        content = '''
import React, { useEffect, useState } from 'react';
import axios from 'axios';

const UserProfile = () => {
    const [user, setUser] = useState(null);
    
    useEffect(() => {
        const fetchUser = async () => {
            try {
                const response = await axios.get(
                    process.env.REACT_APP_API_URL + '/user/profile',
                    {
                        headers: {
                            'Authorization': 'Bearer ' + localStorage.getItem('token')
                        }
                    }
                );
                setUser(response.data);
            } catch (error) {
                console.error('Error:', error);
            }
        };
        
        fetchUser();
    }, []);
    
    return <div>{user ? user.name : 'Loading...'}</div>;
};

export default UserProfile;
'''
        
        with open(self.output_dir / 'UserProfile.js', 'w') as f:
            f.write(content)
    
    def generate_all(self):
        """Генерация всех тестовых файлов"""
        self.generate_simple_api()
        self.generate_obfuscated_api()
        self.generate_react_component()
        
        print(f"✅ Test data generated in {self.output_dir}")

if __name__ == "__main__":
    generator = TestDataGenerator()
    generator.generate_all()
```

---

**[← Назад к навигации](README.md) • [Техническая документация ←](technical.md)**
