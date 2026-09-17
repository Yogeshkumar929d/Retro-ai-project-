const input = document.getElementById("photoInput");
const browse = document.getElementById("browseBtn");
const dropzone = document.getElementById("dropzone");
const fileInfo = document.getElementById("fileInfo");
const fileName = document.getElementById("fileName");
const removeBtn = document.getElementById("removeBtn");
const convertBtn = document.getElementById("convertBtn");
const resultImage = document.getElementById("resultImage");
const emptyState = document.getElementById("emptyState");
const downloadBtn = document.getElementById("downloadBtn");
const generatedPrompt = document.getElementById("generatedPrompt");
const customPrompt = document.getElementById("customPrompt");
const status = document.getElementById("status");
let selectedStyle = "1970s";
let currentPrompt = "";

browse.onclick = () => input.click();
dropzone.onclick = e => { if(e.target.tagName !== "BUTTON") input.click(); };
input.onchange = () => setFile(input.files[0]);

["dragenter","dragover"].forEach(ev => dropzone.addEventListener(ev,e=>{e.preventDefault();dropzone.classList.add("drag")}));
["dragleave","drop"].forEach(ev => dropzone.addEventListener(ev,e=>{e.preventDefault();dropzone.classList.remove("drag")}));
dropzone.addEventListener("drop", e => setFile(e.dataTransfer.files[0]));

document.querySelectorAll(".style-card").forEach(btn=>{
  btn.onclick=()=>{
    document.querySelectorAll(".style-card").forEach(x=>x.classList.remove("active"));
    btn.classList.add("active");
    selectedStyle=btn.dataset.style;
    refreshPrompt();
  };
});

customPrompt.addEventListener("input", refreshPrompt);

function setFile(file){
  if(!file) return;
  input.files = (()=>{ const dt=new DataTransfer(); dt.items.add(file); return dt.files; })();
  fileName.textContent = file.name;
  fileInfo.classList.remove("hidden");
  status.textContent = "Photo ready.";
}
removeBtn.onclick=()=>{
  input.value="";
  fileInfo.classList.add("hidden");
  resultImage.style.display="none";
  emptyState.style.display="block";
  downloadBtn.classList.add("disabled");
  status.textContent="";
};

async function refreshPrompt(){
  try{
    const r=await fetch("/api/prompt",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({style:selectedStyle,customPrompt:customPrompt.value})});
    const data=await r.json();
    currentPrompt=data.prompt;
    generatedPrompt.textContent=currentPrompt;
  }catch(e){}
}
refreshPrompt();

convertBtn.onclick=async()=>{
  const file=input.files[0];
  if(!file){status.textContent="Please choose a photo first.";return;}
  const form=new FormData();
  form.append("photo",file);
  form.append("style",selectedStyle);
  form.append("customPrompt",customPrompt.value);
  convertBtn.disabled=true;
  convertBtn.textContent="Converting...";
  status.textContent="Processing your photo...";
  try{
    const r=await fetch("/api/convert",{method:"POST",body:form});
    const data=await r.json();
    if(!r.ok) throw new Error(data.error||"Conversion failed");
    resultImage.src=data.imageUrl+"?t="+Date.now();
    resultImage.style.display="block";
    emptyState.style.display="none";
    downloadBtn.href=data.downloadUrl;
    downloadBtn.classList.remove("disabled");
    downloadBtn.download=`retro-${selectedStyle.toLowerCase()}-photo.jpg`;
    currentPrompt=data.prompt;
    generatedPrompt.textContent=data.prompt;
    status.textContent=data.mode==="ai" ? "AI conversion complete." : "Retro conversion complete (local demo mode).";
  }catch(e){status.textContent=e.message}
  finally{convertBtn.disabled=false;convertBtn.textContent="✨ Convert Photo";}
};

document.getElementById("copyPromptBtn").onclick=async()=>{
  await navigator.clipboard.writeText(currentPrompt);
  status.textContent="AI prompt copied.";
};
