# v5.5 yeni funksiyalar üçün sınaq (Playwright)
import os, sys, json
from playwright.sync_api import sync_playwright
WWW=os.path.abspath(os.environ.get('WWW','www')); OUT=os.path.abspath('tests/out'); os.makedirs(OUT,exist_ok=True)
CORS={'access-control-allow-origin':'*','access-control-allow-headers':'*','content-type':'application/json'}
fails=[]
def check(n,c,i=''):
    print(('PASS ' if c else 'FAIL ')+n,'' if c else i)
    if not c: fails.append(n)
with sync_playwright() as p:
    b=p.chromium.launch(args=["--no-sandbox","--use-fake-device-for-media-stream","--use-fake-ui-for-media-stream"])
    ctx=b.new_context(viewport={'width':400,'height':800},permissions=['microphone']); pg=ctx.new_page(); errs=[]; reqs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    def gem(route):
        if route.request.method=='OPTIONS': return route.fulfill(status=204,headers=CORS)
        body=route.request.post_data or ''; reqs.append(body[:0]+('AUDIO' if 'inline_data' in body else 'TEXT')); 
        if 'inline_data' in body:
            d=json.loads(body); part=[x for x in d['contents'][0]['parts'] if 'inline_data' in x][0]['inline_data']; reqs.append(('mime',part['mime_type'],part['data'][:5],len(part['data'])))
            return route.fulfill(status=200,headers=CORS,body=json.dumps({'candidates':[{'content':{'parts':[{'text':'Mən Ford Mustangı çox xoşlayıram.'}]}}]}))
        d=json.loads(body)
        if 'proofreader' in json.dumps(d.get('systemInstruction','')):
            lines=json.loads(d['contents'][0]['parts'][0]['text'])['lines']; fixed=[l.replace('xəyəş eləyirəm','xoşlayıram') for l in lines]
            return route.fulfill(status=200,headers=CORS,body=json.dumps({'candidates':[{'content':{'parts':[{'text':json.dumps({'lines':fixed})}]}}]}))
        o={'text':'Mən Ford Mustangı çox xoşlayıram.','title':'Ford Mustang','category':'','remind':'','list':False}
        route.fulfill(status=200,headers=CORS,body=json.dumps({'candidates':[{'content':{'parts':[{'text':json.dumps(o)}]}}]}))
    def google(route):
        if route.request.method=='OPTIONS': return route.fulfill(status=204,headers=CORS)
        route.fulfill(status=200,headers=CORS,body=json.dumps({'results':[{'alternatives':[{'transcript':'Dikte edilmiş mətn'}]}]}))
    pg.route('https://generativelanguage.googleapis.com/**',gem); pg.route('https://speech.googleapis.com/**',google)
    pg.goto('file://'+WWW+'/index.html'); pg.wait_for_timeout(800)
    def mk(title,text='mətn'):
        return pg.evaluate("([a,b])=>{const n={id:Date.now()+Math.floor(Math.random()*999),t:Date.now(),title:a,text:b,html:'',cat:'',files:[]};S.notes.push(n);putN(n);render();return n.id}",[title,text])
    # 1) dəqiq tarix
    a=mk('Not A'); bb=mk('Not B'); pg.wait_for_timeout(200)
    nd=pg.inner_text('.note .nd'); check('exact date under note', any(ch.isdigit() for ch in nd) and ('202' in nd) and ':' in nd, nd)
    # 2) üz qabığı: tək-tək
    pg.evaluate("S.cfg.coverImg=null;saveCfg();render()")
    pg.click('.note >> nth=0'); pg.wait_for_timeout(300); n1=pg.evaluate("fullId")
    check('add-cover button shown when no cover', pg.locator('.covadd').count()==1)
    pg.click('#fCov'); pg.wait_for_timeout(250); pg.click('.cpre[data-k=g2]'); pg.wait_for_timeout(300)
    check('preset cover set on this note', pg.evaluate("byId(%d).coverPreset"%n1)=='g2' and pg.locator('.fcov').count()==1)
    pg.click('#fBack'); pg.wait_for_timeout(300)
    check('list card shows own cover only for that note', pg.locator('.note.hascov').count()==1)
    pg.click('.note.hascov'); pg.wait_for_timeout(300); pg.click('#fCov'); pg.wait_for_timeout(250); pg.click('.cpre[data-k=g5]'); pg.wait_for_timeout(300)
    check('cover changed individually', pg.evaluate("byId(%d).coverPreset"%n1)=='g5')
    pg.click('#fCov'); pg.wait_for_timeout(250); pg.click('[data-a=none]'); pg.wait_for_timeout(300)
    check('no cover for this note', pg.locator('.covadd').count()==1 and pg.evaluate("byId(%d).noCover"%n1))
    pg.click('#fBack'); pg.wait_for_timeout(300)
    pg.evaluate("""async()=>{const c=document.createElement('canvas');c.width=40;c.height=40;const b=await new Promise(r=>c.toBlob(r));S.cfg.coverImg=b;render()}""")
    pg.click('.note >> nth=0'); pg.wait_for_timeout(300); first=pg.evaluate("fullId")
    other=[x for x in pg.evaluate("S.notes.map(n=>n.id)") if x!=n1][0]
    pg.click('#fBack'); pg.wait_for_timeout(300)
    pg.evaluate("openFull(%d)"%n1); pg.wait_for_timeout(300)
    check('per-note "no cover" overrides default cover', pg.locator('.fcov').count()==0 and pg.locator('.covadd').count()==1)
    pg.click('#fCov'); pg.wait_for_timeout(250); pg.click('[data-a=def]'); pg.wait_for_timeout(300)
    check('back to default cover', pg.locator('.fcov').count()==1)
    pg.click('#fBack'); pg.wait_for_timeout(300)
    pg.evaluate("openFull(%d)"%other); pg.wait_for_timeout(300)
    check('other note uses default cover', pg.locator('.fcov').count()==1)
    pg.click('#fBack'); pg.wait_for_timeout(300)
    # 3) notun içində səs yazma (mətn itməməli) — Gemini
    pg.evaluate("S.cfg.keys.gemini='GK';S.cfg.prov='gemini';saveCfg()")
    nid=mk('Səs notu testi','Əvvəlki mətn'); pg.click('.note >> nth=0'); pg.wait_for_timeout(300)
    pg.click('#fMore'); pg.wait_for_timeout(200); pg.click('[data-a=mic]'); pg.wait_for_timeout(2200); pg.click('#rsend')
    pg.wait_for_function("byId(%d).raw"%nid,timeout=15000); pg.wait_for_timeout(1500)
    txt=pg.evaluate("byId(%d).text"%nid); ed=pg.evaluate("document.getElementById('ed').innerText")
    check('dictation lands in the open note', 'Mustang' in txt and 'Mustang' in ed, txt+' | '+ed)
    check('previous text kept', 'Əvvəlki mətn' in txt, txt)
    check('audio attached to note', pg.evaluate("byId(%d).files.filter(f=>f.type.startsWith('audio/')).length"%nid)==1)
    ok=[r for r in reqs if isinstance(r,tuple) and r[0]=='mime']
    check('gemini gets WAV audio', bool(ok) and ok[0][1]=='audio/wav' and ok[0][2]=='UklGR' and ok[0][3]>1000, str(ok[:1]))
    # 4) səs yazısı görünür + silinir
    check('voice recording visible without extra tap', pg.is_visible('#player .adel'))
    pg.click('#player .adel'); pg.wait_for_timeout(300)
    check('voice recording deleted from note', pg.evaluate("byId(%d).files.filter(f=>f.type.startsWith('audio/')).length"%nid)==0)
    # 5) yazılışı yoxla (AI)
    pg.evaluate("(i=>{const n=byId(i);n.text='Mən xəyəş eləyirəm';n.html='';putN(n);openFull(i,true)})(%d)"%nid); pg.wait_for_timeout(300)
    pg.click('#fMore'); pg.wait_for_timeout(200); pg.click('[data-a=spell]'); pg.wait_for_timeout(1500)
    check('spell check fixes words', 'xoşlayıram' in pg.evaluate("byId(%d).text"%nid), pg.evaluate("byId(%d).text"%nid))
    pg.click('#tact'); pg.wait_for_timeout(300)
    check('spell check undo', 'xəyəş' in pg.evaluate("byId(%d).text"%nid))
    pg.click('#fBack'); pg.wait_for_timeout(300)
    # 6) mühərrikləri müqayisə et
    pg.evaluate("S.cfg.keys.google='GG';saveCfg()")
    pg.evaluate("showTest(new Blob([new Uint8Array(4000)],{type:'audio/webm'}),2000,0.5)"); pg.wait_for_timeout(1500)
    rows=pg.locator('.teng').count(); check('compare shows several engines', rows>=2, str(rows))
    pg.evaluate("closePop()")
    # 7) to-do: zoom + zibil
    pg.click('[data-tab=todo]'); pg.wait_for_timeout(250)
    pg.fill('#tdin','Süd al'); pg.press('#tdin','Enter'); pg.wait_for_timeout(200)
    s1=pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.tdt')).fontSize)")
    pg.evaluate("zoomTo(1)"); pg.wait_for_timeout(150); big=pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.tdt')).fontSize)")
    pg.evaluate("zoomTo(4)"); pg.wait_for_timeout(150); small=pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.tdt')).fontSize)")
    check('to-do zoom works', big>s1>small or (big>small), f'{big} {s1} {small}')
    check('slider follows view', pg.evaluate("$('#zoom').value")=='4')
    pg.click('.tdx'); pg.wait_for_timeout(300)
    check('deleted to-do leaves list', pg.locator('.td .tdt').count()==0)
    check('to-do trash chip appears', pg.locator('#tdtr').count()==1)
    pg.click('[data-tab=notes]'); pg.wait_for_timeout(200); pg.click('[data-c=trash]'); pg.wait_for_timeout(250)
    check('trash lists deleted to-do', 'Süd al' in pg.inner_text('#list'))
    pg.click('.tdre'); pg.wait_for_timeout(250); pg.click('[data-tab=todo]'); pg.wait_for_timeout(250)
    check('to-do restored', 'Süd al' in pg.inner_text('#list'))
    pg.click('.tdx'); pg.wait_for_timeout(200); pg.click('[data-tab=notes]'); pg.wait_for_timeout(200); pg.click('[data-c=trash]'); pg.wait_for_timeout(250)
    pg.once('dialog',lambda d:d.accept()); pg.click('#trempty'); pg.wait_for_timeout(300)
    check('empty trash removes to-do for good', pg.evaluate("S.todos.filter(x=>x.text==='Süd al').length")==0)
    check('no JS errors (v5.5 features)', not errs, str(errs))
    b.close()
print('\nFAILED:',fails if fails else 'none'); sys.exit(1 if fails else 0)
