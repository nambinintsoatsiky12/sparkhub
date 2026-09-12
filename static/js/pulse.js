const entries = [
  {name:'Open-Meteo',url:'https://api.open-meteo.com/v1/forecast',description:'Météo mondiale sans clé, idéale pour des agents et prototypes.',category:'Météo',requests_count:12400},
  {name:'REST Countries',url:'https://restcountries.com/v3.1/all',description:'Informations géographiques et politiques sur 250 pays.',category:'Données publiques',requests_count:8900},
  {name:'Open Library',url:'https://openlibrary.org/search.json?q=',description:'Catalogue ouvert de livres, auteurs et éditions du monde entier.',category:'Culture',requests_count:6200},
  {name:'Nominatim',url:'https://nominatim.openstreetmap.org/search',description:'Géocodage basé sur OpenStreetMap, sans compte requis.',category:'Cartographie',requests_count:5100}
];
const icons = {Météo:'☼', 'Données publiques':'◈', Culture:'▤', Cartographie:'⌖'};
const results = document.querySelector('#results'), empty = document.querySelector('#empty');
function render(items){
  results.innerHTML = items.map(x => `<article class="api-card"><div class="api-icon">${icons[x.category] || '◌'}</div><h3>${x.name}</h3><p>${x.description}</p><div class="card-bottom"><span class="status">En ligne</span><span>${(x.requests_count/1000).toFixed(1)}k appels</span></div><div class="api-url" title="${x.url}">${x.url}</div></article>`).join('');
  empty.hidden = items.length > 0;
}
function filter(){const q=document.querySelector('#searchInput').value.toLowerCase();const cat=document.querySelector('.filter.active').dataset.category;render(entries.filter(x=>(!q || `${x.name} ${x.description} ${x.category}`.toLowerCase().includes(q)) && (cat==='Toutes les catégories'||x.category===cat)));}
render(entries);
document.querySelector('#searchForm').addEventListener('submit',e=>{e.preventDefault();filter();document.querySelector('#explorer').scrollIntoView({behavior:'smooth'});});
document.querySelectorAll('[data-query]').forEach(b=>b.addEventListener('click',()=>{document.querySelector('#searchInput').value=b.dataset.query;filter();document.querySelector('#explorer').scrollIntoView({behavior:'smooth'});}));
document.querySelectorAll('.filter').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.filter').forEach(x=>x.classList.remove('active'));b.classList.add('active');filter();}));
const modal=document.querySelector('#modal');
function toggle(open){modal.classList.toggle('open',open);modal.setAttribute('aria-hidden',!open)}
document.querySelector('#openModal').onclick=()=>toggle(true);document.querySelector('#suggest').onclick=()=>toggle(true);document.querySelector('#closeModal').onclick=()=>toggle(false);modal.onclick=e=>{if(e.target===modal)toggle(false)};
document.querySelector('#submitForm').addEventListener('submit',async e=>{e.preventDefault();const msg=document.querySelector('#formMessage');const data=Object.fromEntries(new FormData(e.target));try{const r=await fetch('/api/directory/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const json=await r.json();if(!r.ok)throw Error(json.error);msg.className='form-ok';msg.textContent=json.message;e.target.reset()}catch(err){msg.className='form-error';msg.textContent=err.message||'Une erreur est survenue.'}});