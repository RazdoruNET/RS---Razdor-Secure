import { chromium, Browser, Page, BrowserContext } from 'playwright';

interface XSSConfirmationResult {
  confirmed: boolean;
  evidence: string;
  screenshot?: Buffer;
  error?: string;
}

export class PlaywrightXSSConfirmation {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private page: Page | null = null;

  async initialize(): Promise<void> {
    console.log('🎭 Initializing Playwright for XSS confirmation...');
    
    try {
      this.browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      });
      
      this.context = await this.browser.newContext({
        ignoreHTTPSErrors: true,
        userAgent: 'ProphecySentinel/1.0 Security Assessment Framework'
      });
      
      this.page = await this.context.newPage();
      
      console.log('✅ Playwright initialized successfully');
    } catch (error) {
      console.error(`❌ Failed to initialize Playwright: ${error.message}`);
      throw error;
    }
  }

  async confirmXSS(url: string, payload: string, parameter: string = 'input'): Promise<XSSConfirmationResult> {
    if (!this.page) {
      await this.initialize();
    }

    console.log(`🎭 Confirming XSS at ${url} with payload: ${payload.substring(0, 50)}...`);

    try {
      // Navigate to the URL
      await this.page.goto(url, { waitUntil: 'networkidle', timeout: 10000 });
      
      // Inject payload
      const injectionScript = `
        // Try to inject payload via URL parameter
        const url = new URL(window.location.href);
        url.searchParams.set('${parameter}', '${this.escapeJS(payload)}');
        window.history.replaceState({}, '', url);
        
        // Try to inject payload via form input
        const inputs = document.querySelectorAll('input[name="${parameter}"], textarea[name="${parameter}"]');
        inputs.forEach(input => {
          input.value = '${this.escapeJS(payload)}';
        });
        
        // Try to inject payload via URL hash
        window.location.hash = '${this.escapeJS(payload)}';
      `;

      await this.page.evaluate(injectionScript);
      
      // Wait for potential XSS execution
      await this.page.waitForTimeout(2000);
      
      // Check for XSS execution via alert dialog
      let alertDetected = false;
      this.page.on('dialog', async (dialog) => {
        if (dialog.type() === 'alert') {
          alertDetected = true;
          console.log(`🎭 Alert dialog detected: ${dialog.message()}`);
          await dialog.accept();
        }
      });

      // Try to trigger XSS by interacting with the page
      await this.page.evaluate(() => {
        // Try to trigger events
        const event = new Event('load');
        window.dispatchEvent(event);
        
        // Try to trigger click events
        document.querySelectorAll('a, button, input[type="submit"]').forEach(el => {
          el.click();
        });
      });

      await this.page.waitForTimeout(1000);

      // Check for XSS execution in page content
      const xssDetected = await this.page.evaluate((payload) => {
        // Check if payload is reflected in DOM
        const bodyText = document.body.innerHTML;
        if (bodyText.includes(payload)) {
          return { detected: true, method: 'dom_reflection' };
        }

        // Check for script execution
        const scripts = document.querySelectorAll('script');
        for (const script of scripts) {
          if (script.textContent && script.textContent.includes('alert')) {
            return { detected: true, method: 'script_execution' };
          }
        }

        // Check for event handlers
        const elements = document.querySelectorAll('*');
        for (const el of elements) {
          const attributes = el.getAttributeNames();
          for (const attr of attributes) {
            if (attr.startsWith('on') && el.getAttribute(attr)?.includes('alert')) {
              return { detected: true, method: 'event_handler' };
            }
          }
        }

        return { detected: false, method: 'none' };
      }, payload);

      // Take screenshot for evidence
      const screenshot = await this.page.screenshot({ fullPage: true });

      const confirmed = alertDetected || xssDetected.detected;

      return {
        confirmed,
        evidence: confirmed 
          ? `XSS confirmed via ${xssDetected.method}${alertDetected ? ' + alert dialog' : ''}`
          : 'XSS not confirmed - no execution detected',
        screenshot
      };

    } catch (error) {
      console.error(`❌ XSS confirmation failed: ${error.message}`);
      return {
        confirmed: false,
        evidence: 'XSS confirmation failed due to error',
        error: error.message
      };
    }
  }

  async cleanup(): Promise<void> {
    console.log('🧹 Cleaning up Playwright...');
    
    try {
      if (this.page) {
        await this.page.close();
        this.page = null;
      }
      
      if (this.context) {
        await this.context.close();
        this.context = null;
      }
      
      if (this.browser) {
        await this.browser.close();
        this.browser = null;
      }
      
      console.log('✅ Playwright cleanup completed');
    } catch (error) {
      console.error(`❌ Playwright cleanup failed: ${error.message}`);
    }
  }

  private escapeJS(str: string): string {
    return str
      .replace(/\\/g, '\\\\')
      .replace(/'/g, "\\'")
      .replace(/"/g, '\\"')
      .replace(/\n/g, '\\n')
      .replace(/\r/g, '\\r')
      .replace(/\t/g, '\\t')
      .replace(/\f/g, '\\f')
      .replace(/\v/g, '\\v')
      .replace(/\0/g, '\\0');
  }

  async batchConfirmXSS(targets: Array<{ url: string, payload: string, parameter?: string }>): Promise<XSSConfirmationResult[]> {
    console.log(`🎭 Batch confirming ${targets.length} XSS candidates...`);
    
    const results: XSSConfirmationResult[] = [];
    
    for (const target of targets) {
      const result = await this.confirmXSS(target.url, target.payload, target.parameter);
      results.push(result);
      
      // Small delay between tests
      await this.page?.waitForTimeout(500);
    }
    
    const confirmedCount = results.filter(r => r.confirmed).length;
    console.log(`🎭 Batch confirmation complete: ${confirmedCount}/${targets.length} confirmed`);
    
    return results;
  }
}
