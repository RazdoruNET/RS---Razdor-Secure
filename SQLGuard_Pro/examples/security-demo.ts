import { SQLVulnerabilityScanner } from '../src/core/SQLVulnerabilityScanner';
import { SecurityConfig } from '../src/security/types';
import * as path from 'path';

async function demonstrateSecurity() {
  console.log('🔒 Демонстрация системы безопасности SQL сканера\n');

  // Создаем сканер с настройками безопасности
  const workspaceRoot = path.resolve(__dirname, '..');
  const scanner = new SQLVulnerabilityScanner({}, workspaceRoot);

  try {
    // 1. Инициализация безопасности
    console.log('1️⃣ Инициализация безопасности...');
    await scanner.initialize();
    console.log('✅ Безопасность инициализирована\n');

    // 2. Проверка статуса безопасности
    console.log('2️⃣ Проверка статуса безопасности:');
    const securityStatus = scanner.getSecurityStatus();
    console.log(JSON.stringify(securityStatus, null, 2));
    console.log();

    // 3. Проверка этичных рекомендаций
    console.log('3️⃣ Этические рекомендации:');
    const guidelines = scanner.getEthicalGuidelines();
    guidelines.forEach((guideline, index) => {
      console.log(`${index + 1}. ${guideline}`);
    });
    console.log();

    // 4. Анализ безопасного SQL файла
    console.log('4️⃣ Анализ безопасного SQL файла:');
    const safeSQL = `
      SELECT id, name FROM users 
      WHERE id = ? AND active = 1
    `;
    
    const result = await scanner.analyzeFile(
      path.join(workspaceRoot, 'examples', 'safe-query.sql'),
      safeSQL
    );
    
    console.log(`✅ Анализ завершен. Найдено уязвимостей: ${result.vulnerabilities.length}`);
    console.log();

    // 5. Попытка анализа файла вне доверенной зоны
    console.log('5️⃣ Попытка анализа файла вне доверенной зоны:');
    try {
      await scanner.analyzeFile('/etc/passwd', 'SELECT * FROM users');
    } catch (error) {
      console.log(`✅ Блокировка работает: ${(error as Error).message}`);
    }
    console.log();

    // 6. Проверка отчета безопасности
    console.log('6️⃣ Отчет безопасности:');
    const securityReport = scanner.getOfflineModeManager().generateSecurityReport();
    console.log(JSON.stringify(securityReport, null, 2));
    console.log();

    // 7. Завершение работы
    console.log('7️⃣ Завершение работы...');
    await scanner.shutdown();
    console.log('✅ Работа завершена\n');

  } catch (error) {
    console.error('❌ Ошибка:', error);
  }
}

// Запуск демонстрации
if (require.main === module) {
  demonstrateSecurity().catch(console.error);
}

export { demonstrateSecurity };
