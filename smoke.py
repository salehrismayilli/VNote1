# VNote smoke test (Playwright). İşə sal: python tests/smoke.py  (WWW=www qovluğu)
import os, sys, json, time
from playwright.sync_api import sync_playwright
WWW=os.path.abspath(os.environ.get('WWW','www')); OUT=os.path.abspath('tests/out'); os.makedirs(OUT,exist_ok=True)
CORS={'access-control-allow-origin':'*','access-control-allow-headers':'*','content-type':'application/json'}
fails=[]
CI=bool(os.environ.get('CI'))
def check(name,cond,info=''):
    print(('PASS ' if cond else 'FAIL ')+name,info if not cond else '')
    if not cond: fails.append(name)
with sync_playwright() as p:
    b=p.chromium.launch(args=["--no-sandbox","--use-fake-device-for-media-stream","--use-fake-ui-for-media-stream"])
    ctx=b.new_context(viewport={'width':400,'height':800},permissions=['microphone'])
    pg=ctx.new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    def google(route):
        if route.request.method=='OPTIONS': return route.fulfill(status=204,headers=CORS)
        route.fulfill(status=200,headers=CORS,body=json.dumps({'results':[{'alternatives':[{'transcript':'Məvdən Ford Mustang çox xəyəş eləyirəm'}]}]}))
    def groq(route):
        if route.request.method=='OPTIONS': return route.fulfill(status=204,headers=CORS)
        time.sleep(0.4)
        c={'text':'Mən Ford Mustangı çox xoşlayıram.','title':'Ford Mustang','category':'','remind':'2030-11-03T09:00','list':False}
        route.fulfill(status=200,headers=CORS,body=json.dumps({'choices':[{'message':{'content':json.dumps(c)}}]}))
    pg.route('https://speech.googleapis.com/**',google); pg.route('https://api.groq.com/**',groq)
    pg.goto('file://'+WWW+'/index.html'); pg.wait_for_timeout(700)
    check('version shown', 'v5.5' in pg.inner_text('#count'))
    check('bottom tabs visible', pg.is_visible('#tabbar') and pg.locator('#tabbar button').count()==2)
    mic=pg.locator('#mic').bounding_box(); check('mic on the right', mic['x']>200, str(mic))
    # note + rich text
    try:
        pg.click('#kb'); pg.wait_for_timeout(300); pg.fill('#ft','Test not'); pg.click('#ed'); pg.keyboard.type('Salam dunya hamiya')
        pg.evaluate("()=>{const ln=document.querySelector('#ed .ln');const r=document.createRange();r.setStart(ln.firstChild,0);r.setEnd(ln.firstChild,5);const s=getSelection();s.removeAllRanges();s.addRange(r)}")
        pg.wait_for_timeout(250); pg.click('#sel [data-cmd=strikeThrough]'); pg.wait_for_timeout(200)
        check('strike applied','line-through' in pg.inner_html('#ed'))
        pg.screenshot(path=OUT+'/note.png'); pg.click('#fBack'); pg.wait_for_timeout(400)
        check('note in list','Test not' in pg.inner_text('#list'))
        check('no done circle', pg.locator('.note .chk').count()==0)
    
    except Exception as e:
        check('section: note + rich text',False,str(e)[:300]);pg.screenshot(path=OUT+'/fail-'+str(len(fails))+'.png')
# to-do via bottom tab
    try:
        pg.click('[data-tab=todo]'); pg.wait_for_timeout(250)
        check('mic hidden in todo', not pg.is_visible('#mic'))
        pg.fill('#tdin','Sud al'); pg.press('#tdin','Enter'); pg.wait_for_timeout(200)
        pg.click('.td .tdc'); pg.wait_for_timeout(200)
        check('todo done strike','done' in (pg.get_attribute('.td','class') or ''))
        pg.screenshot(path=OUT+'/todo.png'); pg.click('[data-tab=notes]'); pg.wait_for_timeout(250)
        check('mic back in notes', pg.is_visible('#mic'))
    
    except Exception as e:
        check('section: to-do via bottom tab',False,str(e)[:300]);pg.screenshot(path=OUT+'/fail-'+str(len(fails))+'.png')
# peek -> delete -> trash -> restore
    try:
        bx=pg.query_selector('.note').bounding_box(); pg.mouse.move(bx['x']+50,bx['y']+20); pg.mouse.down(); pg.wait_for_timeout(600); pg.mouse.up(); pg.wait_for_timeout(500)
        check('peek stays', pg.is_visible('#prev')); check('peek has no complete button', pg.locator('[data-pa=done]').count()==0)
        pg.click('[data-pa=del]'); pg.wait_for_timeout(300)
        pg.click('[data-c=trash]'); pg.wait_for_timeout(200); check('in trash','Test not' in pg.inner_text('#list'))
        pg.click('.note'); pg.wait_for_timeout(250); pg.click('[data-a=re]'); pg.wait_for_timeout(250)
        pg.click('[data-c=all]'); pg.wait_for_timeout(200); check('restored','Test not' in pg.inner_text('#list'))
    
    except Exception as e:
        check('section: peek -> delete -> trash -> restore',False,str(e)[:300]);pg.screenshot(path=OUT+'/fail-'+str(len(fails))+'.png')
# image attachment: persistence + instant rotate
    try:
        pg.click('.note'); pg.wait_for_timeout(300)
        pg.evaluate("""async()=>{const c=document.createElement('canvas');c.width=900;c.height=500;const g=c.getContext('2d');g.fillStyle='#e55';g.fillRect(0,0,900,500);g.fillStyle='#fff';g.fillRect(50,50,300,100);
          const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.9));const n=byId(fullId);n.files.push({name:'p.jpg',type:'image/jpeg',blob:b});putN(n);flushN();openFull(n.id)}""")
        pg.wait_for_timeout(500); pg.click('.tile'); pg.wait_for_timeout(400)
        t0=time.time(); pg.click('#vrot'); pg.wait_for_function("document.querySelector('#vimg').style.transform.includes('90')"); dt=(time.time()-t0)*1000
        check('rotate feedback fast', dt<(500 if CI else 150), f'{dt:.0f}ms'); pg.wait_for_timeout(1200)
        sz=pg.evaluate("S.notes[0].files[0].blob.size"); pg.evaluate("flushN()"); pg.wait_for_timeout(300)
        pg.reload(); pg.wait_for_timeout(900)
        sz2=pg.evaluate("S.notes.find(n=>n.files.length).files[0].blob.size"); check('image persists after reload', sz2==sz and sz>1000, f'{sz} vs {sz2}')
    
    except Exception as e:
        check('section: image attachment: persistence + instant rotate',False,str(e)[:300]);pg.screenshot(path=OUT+'/fail-'+str(len(fails))+'.png')
# options + report
    try:
        pg.click('#gear'); pg.wait_for_timeout(300); pg.select_option('[data-os=micSide]','left'); pg.wait_for_timeout(150)
        check('mic side option','mic-left' in pg.evaluate("document.body.className"))
        pg.select_option('[data-os=micSide]','right'); pg.click('#repb'); pg.wait_for_timeout(200)
        check('report has version','VNote v5.5' in pg.inner_text('#rep')); pg.evaluate("closePop();closeSheet()")
    
    except Exception as e:
        check('section: options + report',False,str(e)[:300]);pg.screenshot(path=OUT+'/fail-'+str(len(fails))+'.png')
# cloud STT flow (google + groq mock), progressive text
    try:
        pg.evaluate("S.cfg.keys.google='GK';S.cfg.keys.groq='QK';S.cfg.prov='google';saveCfg()")
        bx=pg.locator('#mic').bounding_box(); pg.mouse.move(bx['x']+40,bx['y']+40); pg.mouse.down(); pg.wait_for_timeout(2000); pg.mouse.up()
        pg.wait_for_function("S.notes.some(n=>n.raw)",timeout=8000)
        first=pg.evaluate("S.notes.find(n=>n.raw).text")
        check('raw text shows first', 'xəyəş' in first or 'Mustangı' in first, first)
        pg.wait_for_function("S.notes.find(n=>n.raw).text.includes('Mustangı')",timeout=8000)
        check('AI refined later', True); check('reminder from command', pg.evaluate("!!S.notes.find(n=>n.raw).remind"))
        check('audio kept', pg.evaluate("S.notes.find(n=>n.raw).files.length")==1)
        pg.screenshot(path=OUT+'/main.png')

    except Exception as e:
        check('section: cloud STT flow (google + groq mock), progressive text',False,str(e)[:300]);pg.screenshot(path=OUT+'/fail-'+str(len(fails))+'.png')
    check('no JS errors', not errs, str(errs))
    b.close()
print('\nFAILED:',fails if fails else 'none'); sys.exit(1 if fails else 0)
