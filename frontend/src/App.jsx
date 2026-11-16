import React, {useMemo, useState} from 'react';
import {Activity, Apple, ArrowUpRight, Camera, ChefHat, CircleUserRound, Clock3, Flame, Leaf, Menu, ScanLine, Settings2, ShieldCheck, ShoppingBasket, Sparkles, Utensils, X} from 'lucide-react';
import {BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell} from 'recharts';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const nav = [
  ['Overview', Activity], ['Food scanner', ScanLine], ['Freshness AI', Apple],
  ['Kitchen safety', ShieldCheck], ['Recipe studio', ChefHat], ['Meal planner', ShoppingBasket]
];
function App(){
  const [page,setPage]=useState('Overview'), [menuOpen,setMenuOpen]=useState(false);
const [provider,setProvider]=useState('gemini'),
      [apiKey,setApiKey]=useState(''),
      [demo,setDemo]=useState(false);
  const [profileOpen,setProfileOpen]=useState(false);
  const [result,setResult]=useState(null), [loading,setLoading]=useState(false), [error,setError]=useState('');
  const [image,setImage]=useState(null), [pantry,setPantry]=useState('chickpeas, spinach, tomatoes, rice, yogurt');
  const [category,setCategory]=useState('Vegetable'), [storage,setStorage]=useState('Refrigerated');
  const [serving,setServing]=useState('1 plate'), [diet,setDiet]=useState('Balanced');
  const [profile,setProfile]=useState({age:24,sex:'Female',weight_kg:60,height_cm:165,activity:'Moderate',goal:'Maintain Weight'});
  const [recipe,setRecipe]=useState(null);
  const fileUrl=useMemo(()=>image?URL.createObjectURL(image):'', [image]);
  const reset=()=>{setResult(null);setError('');setImage(null)};
  async function send(path, formOrBody, isForm=false){
    setLoading(true);setError('');setResult(null);
    try{
      let response;
      if(isForm){formOrBody.append('provider',provider);formOrBody.append('api_key',apiKey);formOrBody.append('demo',String(demo));response=await fetch(`${API}${path}`,{method:'POST',body:formOrBody});}
      else response=await fetch(`${API}${path}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...formOrBody,provider,api_key:apiKey,demo})});
      const data=await response.json(); if(!response.ok) throw new Error(data.detail||'Request failed'); setResult(data);
    }catch(e){setError(e.message||'Could not connect to the Food Verse API.');}
    finally{setLoading(false);}
  }
  function analyzeFood(){
    if(!image){setError('Please upload a food image first.');return;}
    const f=new FormData();f.append('image',image);f.append('serving_context',serving);f.append('dietary_context',diet);send('/api/food/nutrition',f,true);
  }
  function analyzeFresh(){
    if(!image){setError('Please upload a food image first.');return;}
    const f=new FormData();f.append('image',image);f.append('category',category);f.append('storage',storage);send('/api/food/freshness',f,true);
  }
  function analyzeKitchen(){
    if(!image){setError('Please upload a kitchen image first.');return;}
    const f=new FormData();f.append('image',image);send('/api/kitchen/visual-review',f,true);
  }
  function makeRecipe(){send('/api/recipes/generate',{pantry,cuisine:'Indian',dietary:[],max_minutes:35,servings:2});}
  function makePlan(){send('/api/planner/seven-day',{...profile,dietary:[],meals_per_day:3,cuisine:'Indian',exclusions:''});}
  const title=page==='Overview'?'Eat smarter. Live brighter.':page;
  return <div className="app-shell">
    <aside className={`sidebar ${menuOpen?'open':''}`}>
      <div className="brand"><div className="brand-mark"><Apple size={21}/></div><div><b>food verse</b><span>INTELLIGENCE, REIMAGINED</span></div><button className="mobile-close" onClick={()=>setMenuOpen(false)}><X/></button></div>
      <div className="workspace-label">WORKSPACE</div>
      <nav>{nav.map(([label,Icon])=><button key={label} className={`nav-item ${page===label?'active':''}`} onClick={()=>{setPage(label);reset();setMenuOpen(false)}}><Icon size={18}/><span>{label}</span>{label==='Food scanner'&&<i/>}</button>)}</nav>
      <div className="sidebar-bottom">
        <div className="plan-card"><div className="plan-orb"><Sparkles size={17}/></div><b>Your food journey</b><p>Small choices. Better everyday habits.</p><button onClick={()=>setPage('Meal planner')}>Build my plan <ArrowUpRight size={14}/></button></div>
        <button className="profile-row" onClick={()=>setProfileOpen(!profileOpen)}><div className="avatar"><CircleUserRound/></div><div><b>My profile</b><span>Personal workspace</span></div><Settings2 size={17}/></button>
      </div>
    </aside>
    <main className="main">
      <header className="topbar"><button className="mobile-menu" onClick={()=>setMenuOpen(true)}><Menu/></button><div className="crumb">Workspace <span>/</span> {page}</div><div className="top-actions"><span className="status-dot"/> AI SYSTEM {demo?'· DEMO':'· LIVE'} <button className="settings-btn" onClick={()=>setProfileOpen(!profileOpen)}><Settings2 size={17}/></button></div></header>
      <section className="content">
        {profileOpen&&<div className="settings-panel"><div className="panel-head"><b>AI connection</b><button onClick={()=>setProfileOpen(false)}><X size={16}/></button></div><label>Provider<select value={provider} onChange={e=>setProvider(e.target.value)}><option value="gemini">Google Gemini</option><option value="groq">Groq</option></select></label><label>API key<input type="password" placeholder="Paste key for this session" value={apiKey} onChange={e=>setApiKey(e.target.value)}/></label><label className="toggle-line"><input type="checkbox" checked={demo} onChange={e=>setDemo(e.target.checked)}/> Standalone demo mode</label><small>Demo mode uses illustrative sample data and does not analyze uploaded images.</small></div>}
        {page==='Overview'?<>
          <div className="welcome"><div className="welcome-copy"><div className="eyebrow"><span/> YOUR PERSONAL FOOD INTELLIGENCE</div><h1>{title.split('.')[0]}.<br/><em>Live brighter.</em></h1><p>Your everyday companion for understanding what you eat, what you keep, and how you cook.</p><button className="primary-btn" onClick={()=>setPage('Food scanner')}>Scan a meal <ScanLine size={17}/></button><div className="welcome-foot"><span><ShieldCheck size={14}/> Evidence-aware AI</span><span><Leaf size={14}/> Built around better choices</span></div></div><div className="hero-art"><div className="glow glow-one"/><div className="glow glow-two"/><div className="hero-ring ring-one"/><div className="hero-ring ring-two"/><div className="hero-center"><div className="food-emoji">🥑</div><span>FOOD, UNDERSTOOD.</span></div><div className="float-chip chip-a"><Flame size={15}/> Nutrition insights</div><div className="float-chip chip-b"><Sparkles size={15}/> Powered by AI</div><div className="float-chip chip-c"><Leaf size={15}/> Fresh perspective</div></div></div>
          <div className="section-heading"><div><div className="eyebrow dark">EXPLORE YOUR FOODVERSE</div><h2>Your intelligence toolkit</h2></div><span className="muted">Six ways to make food work for you</span></div>
          <div className="feature-grid">{nav.slice(1).map(([label,Icon],i)=><button className={`feature-card feature-${i}`} key={label} onClick={()=>setPage(label)}><div className="feature-icon"><Icon size={20}/></div><span className="feature-index">0{i+1}</span><h3>{label}</h3><p>{['Understand meals with visual nutrition estimates.','Screen visible freshness cues and storage needs.','Review visible kitchen hygiene indicators.','Make something brilliant with what you have.','Build a flexible week around your goals.'][i]}</p><span className="feature-link">Explore <ArrowUpRight size={15}/></span></button>)}</div>
          <div className="bottom-note"><div className="note-icon"><ShieldCheck/></div><div><b>Thoughtful by design</b><p>Food Verse AI provides estimates and decision support—not medical diagnosis, food-safety certification, or a substitute for professional advice.</p></div></div>
        </>:<ToolPage page={page} image={image} setImage={setImage} fileUrl={fileUrl} loading={loading} error={error} result={result} serving={serving} setServing={setServing} diet={diet} setDiet={setDiet} category={category} setCategory={setCategory} storage={storage} setStorage={setStorage} analyzeFood={analyzeFood} analyzeFresh={analyzeFresh} analyzeKitchen={analyzeKitchen} pantry={pantry} setPantry={setPantry} makeRecipe={makeRecipe} recipe={recipe} setRecipe={setRecipe} profile={profile} setProfile={setProfile} makePlan={makePlan}/>}
        <footer><span>FOOD VERSE AI <i>·</i> FOOD INTELLIGENCE, REIMAGINED</span><span>BUILT FOR MORE INFORMED EVERYDAY CHOICES</span></footer>
      </section>
    </main>
  </div>
}
function ToolPage(p){
 const [localError,setLocalError]=useState('');
 const uploadTitle=p.page==='Food scanner'?'Scan your plate':p.page==='Freshness AI'?'Check freshness': 'Review your kitchen';
 const imageTool=['Food scanner','Freshness AI','Kitchen safety'].includes(p.page);
 return <><div className="page-intro"><div className="eyebrow dark">FOOD VERSE / {p.page.toUpperCase()}</div><h1>{p.page}</h1><p>{p.page==='Food scanner'?'A closer look at what is on your plate—ingredients, portions and estimated nutrition.':p.page==='Freshness AI'?'Visual screening for freshness cues, with careful limits and practical storage guidance.':p.page==='Kitchen safety'?'A preliminary visual review of hygiene practices and potential cross-contamination.':p.page==='Recipe studio'?'Turn the ingredients already in your kitchen into something worth looking forward to.':'A flexible seven-day plan shaped around your routine and preferences.'}</p></div>
{imageTool?<>
<div className="tool-layout"><div className="tool-card"><div className="card-title"><div><span className="eyebrow dark">01 / IMAGE INPUT</span><h2>{uploadTitle}</h2></div><Camera/></div><label className="upload-zone"><input type="file" accept="image/png,image/jpeg,image/webp" onChange={e=>p.setImage(e.target.files[0]||null)}/>{p.fileUrl?<img src={p.fileUrl}/>:<><div className="upload-icon"><ScanLine/></div><b>Drop an image or browse files</b><span>JPG, PNG or WEBP · Max 12 MB</span></>}</label>
 {p.page==='Food scanner'&&<><label>Serving context<input value={p.serving} onChange={e=>p.setServing(e.target.value)} placeholder="e.g. one homemade plate"/></label><label>Dietary context<input value={p.diet} onChange={e=>p.setDiet(e.target.value)} placeholder="e.g. vegetarian, low sodium"/></label></>}
 {p.page==='Freshness AI'&&<><label>Food category<select value={p.category} onChange={e=>p.setCategory(e.target.value)}>{['Fruit','Vegetable','Raw meat / poultry','Fish / seafood','Dairy','Other'].map(x=><option>{x}</option>)}</select></label><label>Current storage<select value={p.storage} onChange={e=>p.setStorage(e.target.value)}>{['Unknown','Refrigerated','Room temperature','Frozen','Previously opened'].map(x=><option>{x}</option>)}</select></label></>}
 <button className="primary-btn wide" onClick={p.page==='Food scanner'?p.analyzeFood:p.page==='Freshness AI'?p.analyzeFresh:p.analyzeKitchen} disabled={p.loading}>{p.loading?'Analyzing…':p.page==='Food scanner'?'Analyze my meal':p.page==='Freshness AI'?'Assess visible freshness':'Review kitchen'} <ArrowUpRight size={17}/></button>{p.error&&<div className="error-box">{p.error}</div>}</div>
 <div className="tool-card result-card"><span className="eyebrow dark">02 / INTELLIGENCE REPORT</span><h2>Your results</h2>{p.loading?<div className="loading-state"><div className="loader"/><b>Reading the details…</b><span>Your analysis is being prepared.</span></div>:p.result?<Result result={p.result}/>:<div className="empty-state"><div className="empty-orb"><Sparkles/></div><b>Your report will appear here</b><span>Upload a clear image and start your analysis.</span></div>}</div></div>
 {p.page==='Freshness AI'&&<div className="safety-banner"><ShieldCheck/><span><b>Safety comes first.</b> Visual appearance cannot detect all pathogens or toxins. Never taste-test questionable food.</span></div>}
 {p.page==='Kitchen safety'&&<div className="safety-banner"><ShieldCheck/><span><b>Not a certification.</b> A photo cannot verify handwashing, sanitizer concentration, temperatures, or compliance over time.</span></div>}
 </>:p.page==='Recipe studio'?<div className="tool-card recipe-form"><span className="eyebrow dark">01 / YOUR PANTRY</span><h2>What's in your kitchen?</h2><textarea rows="4" value={p.pantry} onChange={e=>p.setPantry(e.target.value)}/><button className="primary-btn" onClick={p.makeRecipe} disabled={p.loading}>{p.loading?'Creating…':'Create recipes'} <Sparkles size={17}/></button>{p.error&&<div className="error-box">{p.error}</div>}{p.result&&<Result result={p.result}/>}</div>
 :<div className="tool-card recipe-form"><span className="eyebrow dark">01 / YOUR PROFILE</span><h2>Build your weekly rhythm</h2><div className="profile-grid">{[['age','Age'],['weight_kg','Weight (kg)'],['height_cm','Height (cm)']].map(([k,l])=><label>{l}<input type="number" value={p.profile[k]} onChange={e=>p.setProfile({...p.profile,[k]:Number(e.target.value)})}/></label>)}<label>Sex for BMR equation<select value={p.profile.sex} onChange={e=>p.setProfile({...p.profile,sex:e.target.value})}><option>Female</option><option>Male</option><option>Prefer not to specify</option></select></label><label>Activity<select value={p.profile.activity} onChange={e=>p.setProfile({...p.profile,activity:e.target.value})}>{['Sedentary','Light','Moderate','Very active','Extra active'].map(x=><option>{x}</option>)}</select></label><label>Goal<select value={p.profile.goal} onChange={e=>p.setProfile({...p.profile,goal:e.target.value})}>{['Maintain Weight','Fat Loss','Muscle Gain'].map(x=><option>{x}</option>)}</select></label></div><button className="primary-btn" onClick={p.makePlan} disabled={p.loading}>{p.loading?'Building your plan…':'Generate my 7-day plan'} <ArrowUpRight size={17}/></button>{p.error&&<div className="error-box">{p.error}</div>}{p.result&&<Result result={p.result}/>}</div>}
 </>
}
function Result({result:r}){
 if(r.nutrition){const n=r.nutrition;const macros=[{name:'Protein',g:n.protein_g||0},{name:'Carbs',g:n.carbohydrates_g||0},{name:'Fat',g:n.fats_g||0},{name:'Fiber',g:n.fiber_g||0}];return <><div className="result-highlight"><span>HEALTH SCORE</span><strong>{r.health_score??'—'}<small>/100</small></strong><b>{r.dish_name}</b><p>{r.cuisine} · {r.portion_size}</p></div><div className="macro-grid">{[['Calories',`${n.calories_kcal} kcal`],['Protein',`${n.protein_g} g`],['Carbs',`${n.carbohydrates_g} g`],['Fat',`${n.fats_g} g`],['Fiber',`${n.fiber_g} g`]].map(([a,b])=><div><span>{a}</span><b>{b}</b></div>)}</div><div className="chart-box"><b>Macro balance</b><ResponsiveContainer width="100%" height={190}><BarChart data={macros}><XAxis dataKey="name"/><Tooltip/><Bar dataKey="g" fill="#e72b9b" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer></div><b>Ingredients</b><p>{(r.ingredients||[]).join(' · ')}</p><b>Allergen awareness</b><p>{(r.allergens||[]).join(' · ')||'No information returned'}</p><small>{r.confidence_note}</small></>}
 if(r.freshness_stage){return <><div className="result-highlight"><span>VISIBLE FRESHNESS STAGE</span><strong className="stage">{r.freshness_stage}</strong><b>{r.action}</b></div><b>Observations</b>{(r.visual_observations||[]).map(x=><p>• {x}</p>)}<b>Storage tips</b>{(r.storage_tips||[]).map(x=><p>• {x}</p>)}<small>{r.safety_note}</small></>}
 if(r.compliance_score!==undefined){return <><div className="result-highlight"><span>VISUAL COMPLIANCE SCORE</span><strong>{r.compliance_score}<small>%</small></strong></div>{(r.indicators||[]).map(x=><div className="finding"><b>{x.indicator}</b><span>{x.status} · {x.severity}</span><p>{x.observation}</p></div>)}<b>Priority actions</b>{(r.priority_actions||[]).map(x=><p>• {x}</p>)}<small>{r.confidence_note}</small></>}
 if(r.recipes){return r.recipes.map(x=><div className="finding"><span>{x.time_minutes} min · {x.difficulty}</span><h3>{x.name}</h3><p>{x.description}</p><b>Ingredients</b>{(x.ingredients||[]).map(y=><p>• {y}</p>)}<b>Method</b>{(x.instructions||[]).map((y,i)=><p>{i+1}. {y}</p>)}<b>Substitutions</b>{(x.substitutions||[]).map(y=><p>• {y}</p>)}</div>)}
 if(r.meal_plan){return <><div className="result-highlight"><span>ESTIMATED DAILY TARGET</span><strong>{r.energy_estimates?.target_kcal||r.daily_calories}<small>kcal</small></strong><p>BMR {r.energy_estimates?.bmr_kcal} · TDEE {r.energy_estimates?.tdee_kcal}</p></div>{(r.meal_plan||[]).map(d=><div className="finding"><b>{d.day}</b>{(d.meals||[]).map(m=><p>{m.meal}: {m.dish} · ~{m.approximate_calories} kcal</p>)}</div>)}<b>Grocery list</b>{(r.grocery_list||[]).map(x=><p>□ {x.item} — {x.quantity}</p>)}</>}
 return <pre>{JSON.stringify(r,null,2)}</pre>
}
export default App;
