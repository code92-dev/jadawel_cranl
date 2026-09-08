import {
  buildPageDocument,
  BOOTSTRAP_SCRIPT,
} from '@jadawel/modules/arabase/views/utils/pageDocument'

const CSP = "default-src 'none'; connect-src 'none'"

/**
 * The page view renders a document nobody trusted — written by an AI over MCP,
 * or by anyone who can edit the view. The sandbox attribute on the iframe is
 * the first line of defence and the injected policy is the second, so what
 * matters here is that the policy lands *before* any of the author's content,
 * whatever shape that content arrives in.
 */
describe('buildPageDocument', () => {
  const cspTag = (doc) =>
    doc.match(/<meta http-equiv="Content-Security-Policy"[^>]*>/i)

  test('a full document gets the policy as the first thing in its head', () => {
    const doc = buildPageDocument(
      '<!doctype html><html><head><title>Report</title></head><body>hi</body></html>',
      CSP
    )

    const headAt = doc.indexOf('<head>') + '<head>'.length
    expect(doc.slice(headAt)).toMatch(
      /^<meta http-equiv="Content-Security-Policy"/
    )
    // Nothing the author wrote may precede it.
    expect(doc.indexOf('<title>')).toBeGreaterThan(
      doc.indexOf('Content-Security-Policy')
    )
  })

  test('a head with attributes is still matched', () => {
    const doc = buildPageDocument(
      '<html><head lang="ar" data-x="1"><title>t</title></head><body></body></html>',
      CSP
    )

    expect(cspTag(doc)).not.toBeNull()
    expect(doc.indexOf('Content-Security-Policy')).toBeLessThan(
      doc.indexOf('<title>')
    )
  })

  test('a document with no head gets one', () => {
    const doc = buildPageDocument('<html><body>hi</body></html>', CSP)

    expect(doc).toContain('<head>')
    expect(doc.indexOf('Content-Security-Policy')).toBeLessThan(
      doc.indexOf('<body>')
    )
  })

  test('a bare fragment is wrapped into a document', () => {
    const doc = buildPageDocument('<h1>hi</h1>', CSP)

    expect(doc.startsWith('<!doctype html>')).toBe(true)
    expect(doc).toContain('<h1>hi</h1>')
    expect(doc.indexOf('Content-Security-Policy')).toBeLessThan(
      doc.indexOf('<h1>')
    )
  })

  test('a fragment that already declares a doctype does not get a second one', () => {
    const doc = buildPageDocument('<!doctype html><h1>hi</h1>', CSP)

    expect(doc.match(/<!doctype/gi)).toHaveLength(1)
  })

  test('empty and non-string input still produce a policed document', () => {
    for (const input of ['', null, undefined, 42]) {
      const doc = buildPageDocument(input, CSP)
      expect(cspTag(doc)).not.toBeNull()
    }
  })

  test('the policy is escaped so it cannot break out of the attribute', () => {
    const doc = buildPageDocument(
      '<h1>hi</h1>',
      "default-src 'none'; report-uri /x?a=\"><script>alert(1)</script>"
    )

    // The injected quote must not close the content attribute early.
    expect(doc).toContain('&quot;')
    expect(doc).not.toContain('"><script>alert(1)')
  })

  test('every document carries the runtime the contract promises', () => {
    const doc = buildPageDocument('<h1>hi</h1>', CSP)

    expect(doc).toContain(BOOTSTRAP_SCRIPT)
    expect(BOOTSTRAP_SCRIPT).toContain('window.jadawel')
    expect(BOOTSTRAP_SCRIPT).toContain('onData')
  })

  test.each([
    '<!-- <head> --><h1>Report</h1>',
    '<script>const example = "<head>"</script><h1>Report</h1>',
    '<div data-example="<head>">Report</div>',
    '<template><head></head></template><h1>Report</h1>',
    '<script>window.example = true</script><html><head></head></html>',
    '<html data-example=">"><head></head><body>Report</body></html>',
  ])('the trusted head precedes misleading author markup: %s', (html) => {
    const doc = buildPageDocument(html, CSP)
    const parsed = new DOMParser().parseFromString(doc, 'text/html')
    const policy = parsed.head.querySelector(
      'meta[http-equiv="Content-Security-Policy"]'
    )

    expect(policy?.getAttribute('content')).toBe(CSP)
    expect(parsed.head.firstElementChild).toBe(policy)
    expect(doc.indexOf('Content-Security-Policy')).toBeLessThan(
      doc.indexOf(html)
    )
  })

  test.each([undefined, null, '', '  '])(
    'missing policy fails closed: %s',
    (policy) => {
      const doc = buildPageDocument(
        '<script>window.example = true</script>',
        policy
      )
      expect(doc).not.toContain('<script>')
      expect(cspTag(doc)).not.toBeNull()
    }
  )

  test('the bootstrap ignores messages that did not come from the parent', () => {
    // The frame has an opaque origin, so identity is the source window and
    // never event.origin. Guarding on the wrong one is a real mistake, so the
    // check is asserted here rather than left to review.
    expect(BOOTSTRAP_SCRIPT).toContain('event.source !== window.parent')
  })

  test('the bootstrap re-measures after data arrives', () => {
    // The observer only speaks up when the height changes. Without a
    // measurement triggered by the data itself, a parent that missed the first
    // one never hears another, and the frame keeps its placeholder height.
    const onData = BOOTSTRAP_SCRIPT.slice(
      BOOTSTRAP_SCRIPT.indexOf("message.type !== 'jadawel:data'")
    )
    expect(onData).toContain('reportHeight')
  })

  test('the bootstrap contains no closing script tag', () => {
    // It is inlined into <script>…</script>; a literal closer would end the
    // block early and spill the rest of the runtime into the page as markup.
    expect(BOOTSTRAP_SCRIPT.toLowerCase()).not.toContain('</script')
  })
})
