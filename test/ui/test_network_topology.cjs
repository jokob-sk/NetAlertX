// Standalone browser regression for SVG foreignObject rendering; see TESTING_GUIDE.md.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const {chromium, firefox, webkit} = require('playwright');
const {PNG} = require('pngjs');

/** Verify actual painted pixels, since WebKit can report correct bounds for misplaced HTML. */
async function assertPainted(page, selector) {
  const items = await page.locator(selector).all();
  assert(items.length > 0, selector + ' is missing');
  for (const item of items) {
    const rect = await item.boundingBox();
    assert(rect && rect.width > 0 && rect.height > 0, selector + ' has no bounds');
    const png = PNG.sync.read(await page.screenshot({clip: {
      x: Math.ceil(rect.x + 1), y: Math.ceil(rect.y + 2),
      width: Math.max(1, Math.floor(rect.width - 2)), height: Math.max(1, Math.floor(rect.height - 4))
    }}));
    let pixels = 0;
    for (let i = 0; i < png.data.length; i += 4) {
      if (png.data[i] < 240 && png.data[i + 1] < 240 && png.data[i + 2] < 240) pixels++;
    }
    assert(pixels >= 3, selector + ' is not painted at its SVG coordinates');
  }
}

/** Serve the fixture and repository assets on an ephemeral loopback port. */
function createServer() {
  const root = path.resolve(__dirname, '../..');
  return http.createServer((request, response) => {
    const pathname = new URL(request.url, 'http://localhost').pathname;
    const file = path.resolve(root, '.' + pathname);
    if (!file.startsWith(root + path.sep)) {
      response.writeHead(403).end();
      return;
    }
    fs.readFile(file, (error, data) => {
      if (error) {
        response.writeHead(404).end();
        return;
      }
      const types = {'.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript'};
      response.writeHead(200, {'Content-Type': types[path.extname(file)] || 'application/octet-stream'});
      response.end(data);
    });
  });
}

/** Check painting and real pointer interactions before and after tree updates and transforms. */
async function checkBrowser(name, engine, url, artifacts) {
  const browser = await engine.launch();
  try {
    const page = await browser.newPage({viewport: {width: 1200, height: 800}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(url);
    await page.waitForFunction(() => document.querySelectorAll('#networkTree g.node').length === 4);
    // Treeviz transitions take 600 ms; wait for both them and icon fonts to settle.
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(900);
    await page.screenshot({path: path.join(artifacts, name + '-initial.png')});
    for (const selector of ['.spanNetworkTree', '.netIcon', '.portBckgIcon', '.network-hw-icon', '.netCollapse']) {
      await assertPainted(page, '#networkTree ' + selector);
    }
    const laptop = page.locator('.node-inner[data-mac="aa:bb:cc:dd:ee:02"] .spanNetworkTree');
    await laptop.click();
    assert.deepEqual(await page.evaluate(() => clicks), ['aa:bb:cc:dd:ee:02']);
    const collapse = page.locator('.netCollapse[data-mytreemac="aa:bb:cc:dd:ee:01"]');
    await collapse.click();
    await page.waitForFunction(() => document.querySelectorAll('#networkTree g.node').length === 2);
    await page.waitForTimeout(700);
    await collapse.click();
    await page.waitForFunction(() => document.querySelectorAll('#networkTree g.node').length === 4);
    await page.waitForTimeout(700);
    await assertPainted(page, '#networkTree .spanNetworkTree');
    // Exercise Treeviz/D3's actual wheel zoom and drag pan handlers.
    const canvas = page.locator('#networkTree svg > g');
    const beforeZoom = await canvas.getAttribute('transform');
    await page.mouse.move(600, 400);
    await page.mouse.wheel(0, 300);
    await page.waitForTimeout(500);
    const afterZoom = await canvas.getAttribute('transform');
    assert.notEqual(afterZoom, beforeZoom, 'Wheel zoom did not change the SVG transform');
    await page.mouse.move(600, 400);
    await page.mouse.down();
    await page.mouse.move(650, 440, {steps: 5});
    await page.mouse.up();
    assert.notEqual(await canvas.getAttribute('transform'), afterZoom, 'Drag pan did not change the SVG transform');
    await assertPainted(page, '#networkTree .spanNetworkTree');
    await laptop.click();
    assert.equal((await page.evaluate(() => clicks)).length, 2);
    await page.screenshot({path: path.join(artifacts, name + '-zoom-pan.png')});
    // The bundled Treeviz demo expects #tree, which network.php also does not provide.
    assert.deepEqual(errors.filter(error => error !== 'Cannot find dom element with id:tree'), []);
    console.log(name + ': PASS — painting, clicks, collapse/expand, zoom and pan');
  } finally {
    await browser.close();
  }
}

/** Run the same rendering checks in WebKit, Chromium and Firefox without an app backend. */
async function main() {
  const artifacts = process.env.NETALERTX_TOPOLOGY_ARTIFACTS || path.join(os.tmpdir(), 'netalertx-topology');
  fs.mkdirSync(artifacts, {recursive: true});
  const server = createServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const url = `http://127.0.0.1:${server.address().port}/test/ui/fixtures/network_topology.html`;
  try {
    for (const [name, engine] of Object.entries({webkit, chromium, firefox})) {
      await checkBrowser(name, engine, url, artifacts);
    }
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
