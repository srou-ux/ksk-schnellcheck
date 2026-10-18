// Führt den tatsächlichen JavaScript-Code der beiden Seiten aus, ohne Netz und ohne Browser.
// Der kleine DOM-Ersatz prüft Zustandswechsel; Layout und Browserereignisse prüft Playwright separat.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.resolve(__dirname,'../..');

function laden(datei){
  const elemente=new Map();
  const element=id=>{
    if(!elemente.has(id))elemente.set(id,{
      children:[],textContent:'',hidden:false,disabled:false,events:{},
      classList:{remove(){},add(){}},
      addEventListener(name,fn){this.events[name]=fn},
      replaceChildren(...xs){this.children=xs},
    });
    return elemente.get(id);
  };
  const context=vm.createContext({
    document:{getElementById:element,querySelector:element},
    fetch:()=>new Promise(()=>{}), // Initiales Laden der Optionen bleibt aus.
  });
  const html=fs.readFileSync(path.join(root,datei),'utf8');
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],context);
  return {context,element,run:code=>vm.runInContext(code,context)};
}

test('Beträge behalten ihren Wert; kaputte Trennzeichen werden abgelehnt',()=>{
  const {context:c}=laden('schnellcheck/static/index.html');
  for(const [eingabe,soll] of [
    ['1250','1250'],['1250.5','1250.5'],['1250,5','1250.5'],['1.250,00','1250.00'],
    ['1.250','1250'],['1.234.567,89','1234567.89'],[' 1250,00 € ','1250.00'],['0,01','0.01'],
    ['',null],['   ',null],
  ])assert.equal(c.betragText(eingabe),soll,eingabe);
  for(const s of ['12,345','1,250.00','12.34,56','1,2,3','1 2','1€2','12,','1.2345','-1','NaN','Infinity'])
    assert.equal(c.betragText(s),'ungueltig',s);
});

test('Änderungen an Eingaben entfernen das bisherige Ergebnis',()=>{
  const {element}=laden('schnellcheck/static/index.html');
  for(const event of ['input','change']){
    element('ergebnis').children=['altes Ergebnis'];
    element('formular').events[event]();
    assert.equal(element('ergebnis').children.length,0,event);
  }
});

function prueflauf(){
  const s=laden('schnellcheck/static/index.html');
  const antworten=[],anzeigen=[];
  s.context.sammeln=()=>({fall:{},fehler:[]});
  s.context.zeigen=d=>anzeigen.push(d);
  s.context.fetch=()=>new Promise((resolve,reject)=>antworten.push({
    ok:d=>resolve({ok:true,json:async()=>d}),fehler:reject,
  }));
  return {...s,antworten,anzeigen,start:()=>s.context.pruefen({preventDefault(){}})};
}

test('Verspätete Antwort nach einer Änderung wird verworfen',async()=>{
  const s=prueflauf();const p=s.start();
  s.element('formular').events.input();s.antworten[0].ok({alt:true});await p;
  assert.equal(s.anzeigen.length,0);
  assert.equal(s.element('pruefen').disabled,false);
  const neu=s.start();s.antworten[1].ok({neu:true});await neu;
  assert.equal(s.anzeigen.length,1);
  assert.equal(s.anzeigen[0].neu,true);
});

test('Verspätete Fehlermeldung gehört nicht zum geänderten Formular',async()=>{
  const s=prueflauf();const p=s.start();s.context.verwerfen();
  s.antworten[0].fehler(Error('alter Fehler'));await p;
  assert.equal(s.element('meldung').textContent,'');
  assert.equal(s.element('pruefen').disabled,false);
});

test('Bei überlappenden Anfragen zählt nur die neueste',async()=>{
  const s=prueflauf();const alt=s.start(),neu=s.start();
  s.antworten[0].ok({alt:true});await alt;
  assert.equal(s.element('pruefen').disabled,true);
  s.antworten[1].ok({neu:true});await neu;
  assert.equal(s.anzeigen.length,1);assert.equal(s.anzeigen[0].neu,true);
});

test('Validierungsfehler lassen kein altes Ergebnis stehen',async()=>{
  const s=prueflauf();s.element('ergebnis').children=['alt'];
  s.context.sammeln=()=>({fall:{},fehler:['Betrag ungültig']});await s.start();
  assert.equal(s.element('ergebnis').children.length,0);
  assert.equal(s.antworten.length,0);
});

test('CSV neutralisiert Formeln, auch hinter Leer- und Steuerzeichen',()=>{
  const {context:c}=laden('app/static/dokumente.html');
  for(const s of ['=1+1','+1+1','-1+1','@SUM(A1)','  =1+1','\t=1+1','\u0000=1+1'])
    assert.equal(c.csvFeld(s),"'"+s);
  assert.equal(c.csvFeld('Logo; Design'),'"Logo; Design"');
  assert.equal(c.csvFeld('Zeile\rText'),'"Zeile\rText"');
  assert.equal(c.csvFeld('1200,00'),'1200,00');
});

test('Verworfenes Dokumentergebnis kann nicht mehr exportiert werden',()=>{
  const s=laden('app/static/dokumente.html');
  s.run('letztesErgebnis={ergebnisklasse:"alt"}; invalidate();');
  assert.equal(s.run('letztesErgebnis'),null);
  s.context.csvSpeichern(); // Ohne Ergebnis darf kein Download erzeugt werden.
});


test('Dokumentfelder werden vorbelegt, manuelle Korrekturen bleiben erhalten',()=>{
  const s=laden('app/static/dokumente.html');
  const v=wert=>({formularvorschlaege:{unternehmensart:{wert,beleg:'Rechnungsempfänger: '+wert}}});
  s.element('company').value='';
  s.context.uebernehmen(v('Bäckerei Test'),'rechnung.pdf');
  assert.equal(s.element('company').value,'Bäckerei Test');
  assert.match(s.element('autofill-note').textContent,/rechnung.pdf/);
  s.element('company').value='Meine Korrektur';
  s.element('facts').events.input({target:{id:'company'}});
  s.context.uebernehmen(v('Andere Firma'),'zweite.pdf');
  assert.equal(s.element('company').value,'Meine Korrektur');
  assert.match(s.element('autofill-note').textContent,/Unterschiedliche/);
});

test('Widersprechende Empfänger entfernen eine automatische Vorbelegung',()=>{
  const s=laden('app/static/dokumente.html');
  const v=wert=>({formularvorschlaege:{unternehmensart:{wert,beleg:wert}}});
  s.element('company').value='';
  s.context.uebernehmen(v('Firma A'),'a.pdf');
  s.context.uebernehmen(v('Firma B'),'b.pdf');
  assert.equal(s.element('company').value,'');
  s.context.uebernehmen(v('Firma C'),'c.pdf');
  assert.equal(s.element('company').value,'');
});
