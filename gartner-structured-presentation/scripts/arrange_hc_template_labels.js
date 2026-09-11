async (page) => {
  await page.setViewportSize({width:1600,height:950});
  const result=await page.evaluate(()=>{
    const svg=document.querySelector('#chart');
    const labels=[...svg.querySelectorAll('.tech-label')];
    const trackPoints=[...svg.querySelectorAll('[data-template-role="annual-track"] path')].flatMap(p=>{const len=p.getTotalLength();return Array.from({length:240},(_,i)=>{const q=p.getPointAtLength(i*len/239);return {x:q.x,y:q.y};});});
    const dots=[...svg.querySelectorAll('[data-year][data-technology]')].map(n=>({x:+n.dataset.x,y:+n.dataset.y}));
    const fixed=[{x:932,y:40,w:213,h:95},{x:43,y:92,w:73,h:18}];
    const placed=[],leaders=[];
    const overlaps=(a,b,pad=3)=>a.x<b.x+b.w+pad&&a.x+a.w+pad>b.x&&a.y<b.y+b.h+pad&&a.y+a.h+pad>b.y;
    const inside=(q,b,pad=3)=>q.x>b.x-pad&&q.x<b.x+b.w+pad&&q.y>b.y-pad&&q.y<b.y+b.h+pad;
    const cross=(a,b,c,d)=>{const cc=(p,q,r)=>(r.y-p.y)*(q.x-p.x)>(q.y-p.y)*(r.x-p.x);return cc(a,c,d)!==cc(b,c,d)&&cc(a,b,c)!==cc(a,b,d);};
    const infos=labels.map(n=>{const b=n.getBBox();return {n,px:+n.dataset.pointX,py:+n.dataset.pointY,w:b.width,h:b.height,dx:b.x-(+n.getAttribute('x')),dy:b.y-(+n.getAttribute('y'))};});
    // Dense summit first, then wider labels: preserve point geometry completely.
    infos.sort((a,b)=>{const da=dots.filter(q=>Math.hypot(q.x-a.px,q.y-a.py)<60).length;const db=dots.filter(q=>Math.hypot(q.x-b.px,q.y-b.py)<60).length;return db-da||b.w-a.w;});
    for(const q of infos){
      const candidates=[];
      for(let r=28;r<=250;r+=12)for(let i=0;i<40;i++){const angle=i*Math.PI/20;const cx=q.px+Math.cos(angle)*r,cy=q.py+Math.sin(angle)*r;candidates.push({x:cx-q.w/2,y:cy-q.h/2,w:q.w,h:q.h});}
      let best=null,bestScore=Infinity;
      for(const b of candidates){
        if(b.x<82||b.x+b.w>1115||b.y<66||b.y+b.h>489)continue;
        if(fixed.some(f=>overlaps(b,f,6)))continue;
        if(placed.some(p=>overlaps(b,p,5)))continue;
        if(dots.some(p=>inside(p,b,7)))continue;
        const center={x:b.x+b.w/2,y:b.y+b.h/2};
        let score=Math.hypot(center.x-q.px,center.y-q.py);
        score+=trackPoints.filter(p=>inside(p,b,3)).length*90;
        score+=leaders.filter(l=>cross({x:q.px,y:q.py},center,l.a,l.b)).length*12;
        score+=placed.filter(p=>Array.from({length:12},(_,i)=>({x:q.px+(center.x-q.px)*i/12,y:q.py+(center.y-q.py)*i/12})).some(x=>inside(x,p))).length*35;
        if(score<bestScore){best=b;bestScore=score;}
      }
      if(!best)throw Error('No clean position for '+q.n.dataset.name);
      q.n.setAttribute('x',best.x-q.dx);q.n.setAttribute('y',best.y-q.dy);
      q.n.querySelectorAll('tspan').forEach(t=>t.setAttribute('x',best.x-q.dx));
      q.n.dataset.originalX=q.n.getAttribute('x');q.n.dataset.originalY=q.n.getAttribute('y');
      const c={x:best.x+best.w/2,y:best.y+best.h/2},vx=q.px-c.x,vy=q.py-c.y;
      const t=Math.min(Math.abs(vx)<.001?Infinity:(best.w/2+2)/Math.abs(vx),Math.abs(vy)<.001?Infinity:(best.h/2+2)/Math.abs(vy),1);
      const end={x:c.x+vx*t,y:c.y+vy*t};
      const p=svg.querySelector('.dynamic-leader[data-for="'+q.n.dataset.name+'"]');p.setAttribute('d',`M ${q.px} ${q.py} L ${end.x} ${end.y}`);p.classList.remove('too-far');
      placed.push(best);leaders.push({a:{x:q.px,y:q.py},b:end});
    }
    return {labels:labels.length,maxLeader:Math.max(...leaders.map(l=>Math.hypot(l.a.x-l.b.x,l.a.y-l.b.y))),positions:labels.map(n=>({id:n.dataset.name,x:n.getAttribute('x'),y:n.getAttribute('y')}))};
  });
  if(result.maxLeader>232)throw Error('Leader exceeds the template limit; revise label layout before export');
  for(const [button,file] of [['#exportSvg','hc-comparison.svg'],['#exportPng','hc-comparison.png'],['#saveLayout','hc-comparison-layout.json']]){
    const promise=page.waitForEvent('download');await page.locator(button).click();await (await promise).saveAs(file);
  }
  try { await page.screenshot({path:'hc-layout-preview.png',fullPage:true,timeout:5000}); result.editorScreenshot='saved'; } catch(e) { result.editorScreenshot='unavailable; inspect exported PNG separately'; }
  console.log(JSON.stringify(result));
}
