const fs=require('fs');
const src=fs.readFileSync(''+__dirname+'/../src/index.html','utf8');
const grab=(name)=>{const i=src.indexOf('const '+name+' = ');let j=src.indexOf('{',i),d=0,k=j;for(;k<src.length;k++){if(src[k]=='{')d++;else if(src[k]=='}'){d--;if(!d)break;}}return eval('('+src.slice(j,k+1)+')');};
const N=grab('N'),P=grab('PROFILES'),E=grab('ENDINGS'),PAT=grab('PATIENTS'),R=grab('ROUNDS');
const nm={J:'Hr. Jensen',H:'Fru Hansen',A:'Ahmed',B:'Birthe'};
let o=`# Historietræet\n\nAlle 31 situationer (noder) og 32 slutninger, trukket direkte ud af \`N\`, \`ENDINGS\` og \`PROFILES\` i [src/index.html](../src/index.html) (afsnit [K2] og [K3]). Filen er genereret, så den altid matcher koden.\n\n**Sådan læses node-ID'et:** \`R3-AB\` = runde 3, efter valg **A** i runde 1 og **B** i runde 2. A og B fører videre. X1 og X2 er de \"skøre\" valg, der giver game over (☠️ patienten dør, 🚫 du bliver fyret).\n\n## Patienterne\n\n| Kode | Stue | Navn | Info |\n|---|---|---|---|\n`;
for(const k in PAT)o+=`| ${k} | ${PAT[k].no} | ${PAT[k].nm} | ${PAT[k].info} |\n`;
o+=`\n## Runderne\n\n| Runde | Tema | Sted |\n|---|---|---|\n`;
for(const k in R)o+=`| ${k} | ${R[k].theme} | ${R[k].room} |\n`;
o+=`\n## Overblik\n\n\`\`\`mermaid\nflowchart LR\n`;
const ids=Object.keys(N);
const nid=id=>id.replace('-','_');
ids.forEach(id=>{o+=`  ${nid(id)}["${id}<br/>${N[id].title.replace(/"/g,"'")}"]\n`;});
ids.forEach(id=>{const r=+id[1],p=id.split('-')[1]||'';if(r<5){for(const c of 'AB'){o+=`  ${nid(id)} -- ${c} --> ${nid('R'+(r+1)+'-'+p+c)}\n`;}}});
o+='```\n';
for(let r=1;r<=5;r++){
 o+=`\n## Runde ${r} · ${R[r].theme}\n`;
 ids.filter(id=>id[1]==r).forEach(id=>{const n=N[id];
  o+=`\n### ${id} · ${n.title}${n.alarm?' 🚨':''}\n\n*Patienter:* ${[...n.f].map(x=>nm[x]).join(', ')}\n\n${n.sit}\n\n| Valg | Tekst | Udfald |\n|---|---|---|\n`;
  for(const k of ['A','B','X1','X2']){const c=n.c[k];
   const next=k.length==1?(r<5?'→ R'+(r+1)+'-'+(id.split('-')[1]||'')+k:'→ slutning'):(c[2]=='død'?'☠️ '+c[1]:'🚫 '+c[1]);
   o+=`| ${k} | ${c[0].replace(/\|/g,'/')} | ${next} |\n`;}
  o+=`\n> **Feedback:** ${n.fb}\n`;});
}
o+=`\n## De 32 slutninger\n\nProfilen afhænger af antal A-valg (systemets vej): ${Object.keys(P).sort((a,b)=>b-a).map(k=>k+' A = '+P[k]).join(' · ')}.\n\n| Vej | Profil | Slutning |\n|---|---|---|\n`;
Object.keys(E).forEach(p=>{o+=`| ${p} | ${P[(p.match(/A/g)||[]).length]} | ${E[p]} |\n`;});
fs.writeFileSync(''+__dirname+'/../docs/historier.md',o);
console.log(ids.length, Object.keys(E).length, o.length);
