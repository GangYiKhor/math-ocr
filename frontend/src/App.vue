<script setup>
import { ref } from 'vue';
import UploadIcon from './components/UploadIcon.vue';
import PencilIcon from './components/PencilIcon.vue';
import EraserIcon from './components/EraserIcon.vue';
import TrashIcon from './components/TrashIcon.vue';
import ClearImageIcon from './components/ClearImageIcon.vue';
import AddImageIcon from './components/AddImageIcon.vue';
import LineIcon from './components/LineIcon.vue';
import RectangleIcon from './components/RectangleIcon.vue';
import TriangleIcon from './components/TriangleIcon.vue';
import OvalIcon from './components/OvalIcon.vue';
import DotIcon from './components/DotIcon.vue';
import CopyIcon from './components/CopyIcon.vue';

const urlCreator = window.URL || window.webkitURL;
const expectedFileTypes = new Set(['image/jpeg', 'image/png']);
const modes = [
  { mode: 'draw', icon: PencilIcon },
  { mode: 'erase', icon: EraserIcon },
  { mode: 'line', icon: LineIcon },
  { mode: 'rectangle', icon: RectangleIcon },
  { mode: 'triangle', icon: TriangleIcon },
  { mode: 'oval', icon: OvalIcon },
];
const sizes = [3, 5, 7, 11, 15];

const btnFileUpload = ref();
const btnFileAdd = ref();
const spanCopy = ref();
const downloadForm = ref();

const draggedOver = ref();
const dragOverTimeout = ref();
const isAnalysing = ref();

const images = ref(new Map());
const results = ref(new Map());

const selectedUuid = ref();
const selectedMode = ref(modes[0].mode);
const selectedSize = ref(sizes[Math.floor((sizes.length - 1) / 2)]);

function readFile(file, callback) {
  if (!expectedFileTypes.has(file.type)) return;

  const fileReader = new FileReader();
  fileReader.readAsArrayBuffer(file);
  fileReader.onloadend = function () {
    const blob = new Blob([fileReader.result], { type: file.type });
    const url = urlCreator.createObjectURL(blob);
    callback(url, blob);
  };
}

function loadFile(file, select = false) {
  readFile(file, function (url, blob) {
    let uuid = url.split('/').at(-1);
    while (images.value.has(uuid)) uuid += '_1';
    images.value.set(uuid, { url, blob });

    if (select) selectedUuid.value = uuid;
  });
}

function loadFiles(files, selectLast = true) {
  const length = files.length;
  let i = 0;
  for (const file of files) {
    i++;
    loadFile(file, selectLast && i === length);
  }
}

function dragOver() {
  clearTimeout(dragOverTimeout.value);
  draggedOver.value = true;
}

function dragEnd() {
  dragOverTimeout.value = setTimeout(() => (draggedOver.value = false), 100);
}

function dropFiles(event) {
  draggedOver.value = false;
  if (event.target.id !== 'image-dropper') return;
  loadFiles(event.dataTransfer.files);
}

function uploadFile() {
  btnFileUpload.value.click();
}

function onUploadFile(event) {
  loadFiles(event.currentTarget.files);
  btnFileUpload.value.value = null;
}

function removeFile(uuid) {
  images.value.delete(uuid);
}

function emptyImage() {
  const url = urlCreator.createObjectURL(new Blob([new ArrayBuffer(0)]));
  let uuid = url.split('/').at(-1);
  while (images.value.has(uuid)) uuid += '_1';
  images.value.set(uuid, null);
  selectedUuid.value = uuid;
}

function clearImage() {
  if (selectedUuid.value) images.value.set(selectedUuid.value, null);
}

function addImage() {
  btnFileAdd.value.click();
}

function onAddImage(event) {
  for (const file of event.currentTarget.files) {
    readFile(file, function (url, blob) {
      if (selectedUuid.value) images.value.set(selectedUuid.value, { url, blob });
    });
    break;
  }
  btnFileAdd.value.value = null;
}

function selectFile(uuid) {
  selectedUuid.value = uuid;
}

async function analyse(uuid) {
  if (isAnalysing.value) return;

  const image = images.value.get(uuid)?.blob;
  if (!image) return;

  try {
    isAnalysing.value = true;
    const formData = new FormData();
    formData.append('file', image);

    const response = await fetch('http://127.0.0.1:8000/analyse', { method: 'POST', body: formData });
    const output = (await response.json()).output;
    const latex = output.latex;
    const omml = output.omml;
    const mathml = output.mathml;
    const html = buildSvg(latex);

    if (html[0] == '<br/>') html.shift(1);
    results.value.set(uuid, { html, latex, omml, mathml });
  } catch {
    results.value.set(uuid, {
      html: ['<div class="analysis-failed"><p>Analysis Failed!</p><p>The image is too complex!</p></div>'],
    });
  } finally {
    isAnalysing.value = false;
  }
}

const mathRegex = /\\(begin|end)\{math\}/gi;
function buildSvg(latex = []) {
  const html = [];

  for (const line of latex) {
    if (line === '\n') {
      html.push('<br/>');
    } else if (line.includes('\n')) {
      html.push(...buildSvg(line.split('\n')));
    } else if (line.match(/\\/gi)) {
      const text = line.replaceAll(mathRegex, '').trim();
      if (text === '') continue;
      try {
        html.push(MathJax.tex2svg(text).outerHTML);
      } catch {
        // If fail, skip it
      }
    } else {
      html.push(`<span>${line.trim()}</span>`);
    }
  }

  return html;
}

function download() {
  downloadForm.value.method = 'POST';
  downloadForm.value.action = 'http://127.0.0.1:8000/download';
  downloadForm.value.target = '';
  downloadForm.value.submit();
}

function copy(mathml) {
  navigator.permissions.query({ name: 'clipboard-write' }).then((result) => {
    if (result.state === 'granted') {
      let text = mathml.join('');
      if ((text.match(new RegExp('http://www.w3.org/1998/Math/MathML', 'g')) || []).length > 1) {
        text = text.split('<math xmlns="http://www.w3.org/1998/Math/MathML"').join('\n\n<math xmlns="http://www.w3.org/1998/Math/MathML"');
      }

      const blob = new Blob([text.trim()], { type: 'text/plain' });
      ``;
      const item = new ClipboardItem({ 'text/plain': blob });

      navigator.clipboard.write([item]).then(
        () => {
          spanCopy.value.textContent = 'Copied!';
          setTimeout(() => (spanCopy.value.textContent = 'Copy'), 2000);
        },
        () => console.error('Unable to write to clipboard. Error:'),
      );
    } else {
      spanCopy.value.textContent = 'No permission to copy!';
      setTimeout(() => (spanCopy.value.textContent = 'Copy'), 2000);
    }
  });
}
</script>

<template>
  <main
    @dragover.prevent="dragOver"
    @dragleave.prevent="dragEnd"
    @dragend.prevent="dragEnd"
    @drop.prevent="dropFiles"
    class="h-screen flex flex-col justify-center items-center bg-neutral-200"
  >
    <h1 class="mb-4 font-bold tracking-wider text-5xl">Math OCR</h1>

    <div class="h-[87%] w-[90%] grid grid-rows-[calc(var(--spacing)*30)_calc(var(--spacing))_1fr] bg-white border-cyan-800 border-4 rounded-t-xl">
      <div class="relative h-30 w-full px-0.5 overflow-x-auto overflow-y-hidden scroll-smooth text-nowrap horizontal-custom-scrollbar">
        <div v-for="item of images.entries()" :key="item[0]" class="relative h-full w-20 p-1 inline-block">
          <div @click="selectFile(item[0])" class="relative h-full w-full border-2 rounded-sm bg-gray-200 cursor-pointer hover:brightness-90 active:brightness-80 select-none">
            <img v-if="item[1]" :src="item[1]?.url" :alt="`img-${item[0]}`" class="h-full w-full rounded-sm object-contain" />
          </div>

          <button
            @click="removeFile(item[0])"
            class="absolute z-10 right-0 top-0 px-1.5 pb-1 text-xs text-red-500 font-bold bg-red-100 border-2 border-red-500 rounded-full cursor-pointer hover:bg-red-200 active:bg-red-300 transition-colors"
          >
            x
          </button>
        </div>

        <div class="h-full w-20 p-1 inline-block">
          <div @click="uploadFile" class="relative h-full w-full border-2 rounded-sm cursor-pointer hover:bg-neutral-200 active:bg-neutral-300 select-none">
            <div class="absolute w-full h-full flex justify-center items-center">
              <UploadIcon width="30" height="30" />
            </div>
          </div>
        </div>

        <div class="h-full w-20 p-1 inline-block">
          <div @click="emptyImage" class="relative h-full w-full border-2 rounded-sm cursor-pointer hover:bg-neutral-200 active:bg-neutral-300 select-none">
            <span class="absolute top-1/4 left-1/4 w-1/2 h-1/2 flex justify-center items-center font-bold text-2xl">+</span>
          </div>
        </div>

        <input @change="onUploadFile" type="file" class="hidden" ref="btnFileUpload" accept=".jpg,.png" multiple />
      </div>

      <hr class="border-2 border-cyan-800" />

      <div class="relative flex-1 h-full grid grid-cols-2 grid-rows-1">
        <div class="absolute z-10 -left-12 -top-1 flex flex-col bg-white border-4 border-r-0" :class="{ hidden: !images.has(selectedUuid) }">
          <button
            v-for="mode of modes"
            :key="mode.mode"
            @click="selectedMode = mode.mode"
            class="w-10 h-10 flex justify-center items-center cursor-pointer hover:brightness-90 active:brightness-80"
            :class="{ 'bg-slate-300': selectedMode === mode.mode, 'bg-white': selectedMode !== mode.mode }"
          >
            <component :is="mode.icon" width="30" height="30" />
          </button>

          <button class="w-10 h-10 flex justify-center items-center cursor-pointer bg-white hover:brightness-90 active:brightness-80">
            <TrashIcon width="30" height="30" />
          </button>

          <button @click="addImage" class="w-10 h-10 flex justify-center items-center cursor-pointer bg-white hover:brightness-90 active:brightness-80">
            <AddImageIcon width="30" height="30" />
            <input @change="onAddImage" type="file" class="hidden" ref="btnFileAdd" accept=".jpg,.png" />
          </button>

          <button @click="clearImage" class="w-10 h-10 flex justify-center items-center cursor-pointer bg-white hover:brightness-90 active:brightness-80">
            <ClearImageIcon width="30" height="30" />
          </button>

          <hr class="my-4 border-2" />

          <button
            v-for="size of sizes"
            :key="size"
            @click="selectedSize = size"
            class="w-10 h-10 flex justify-center items-center cursor-pointer hover:brightness-90 active:brightness-80"
            :class="{ 'bg-slate-300': selectedSize === size, 'bg-white': selectedSize !== size }"
          >
            <DotIcon :width="size" :height="size" />
          </button>
        </div>

        <div class="relative h-full border-r-2 border-cyan-800">
          <div id="image-dropper" class="absolute top-1/8 left-1/8 h-3/4 w-3/4 m-auto border-4 border-gray-400 border-dashed"></div>

          <div v-if="!draggedOver" class="absolute w-full h-full p-1 pb-0 flex justify-center bg-white overflow-auto">
            <div class="relative w-full min-h-full h-fit pb-1">
              <img v-if="images.get(selectedUuid)?.url" :src="images.get(selectedUuid)?.url" class="w-full border-2 border-gray-400" />
              <div class="absolute top-0 z-10 w-full h-[calc(100%-var(--spacing))] border-2" :class="{ 'cursor-crosshair': images.has(selectedUuid) }"></div>
            </div>
          </div>
        </div>

        <form ref="downloadForm" class="relative h-full border-l-2 border-cyan-800">
          <div class="absolute h-[93.5%] w-full p-2 overflow-auto">
            <div v-for="html of results.get(selectedUuid)?.html?.entries()" :key="`latex-${html[0]}`" v-html="html[1]"></div>
          </div>

          <div class="absolute z-10 bottom-0 right-0 p-1 flex gap-2 font-bold font-[Consolas,monospace] border-t-2 border-l-2">
            <button
              @click.prevent="copy(results.get(selectedUuid)?.mathml)"
              v-show="results.get(selectedUuid)?.mathml"
              :disabled="!results.get(selectedUuid)?.mathml"
              class="group px-3 py-1 flex items-center gap-1 border-1 border-[rgb(153,159,165)] bg-white enabled:hover:bg-[rgb(108,117,125)] enabled:active:bg-[rgb(85,92,100)] disabled:opacity-50 text-black hover:text-white active:text-white transition-colors"
              :class="{ 'cursor-not-allowed': !results.get(selectedUuid)?.mathml, 'cursor-pointer': results.get(selectedUuid)?.mathml }"
            >
              <CopyIcon width="20" height="20" colour="black" class="group-hover:invert group-active:invert" />
              <span ref="spanCopy">Copy</span>
            </button>

            <button
              @click.prevent="analyse(selectedUuid)"
              :disabled="!selectedUuid || isAnalysing"
              class="px-3 py-1 bg-[rgb(40,167,69)] enabled:hover:bg-[rgb(33,136,56)] enabled:active:bg-[rgb(30,126,52)] disabled:opacity-50 text-white transition-colors"
              :class="{ 'cursor-wait': isAnalysing, 'cursor-not-allowed': !selectedUuid, 'cursor-pointer': selectedUuid && !isAnalysing }"
            >
              Analyse
            </button>

            <button
              @click.prevent="download(results.get(selectedUuid)?.latex)"
              v-show="results.get(selectedUuid)?.latex"
              :disabled="!results.get(selectedUuid)?.latex"
              ref="btnDownload"
              class="px-3 py-1 bg-[rgb(23,162,184)] enabled:hover:bg-[rgb(19,132,150)] enabled:active:bg-[rgb(17,122,139)] disabled:opacity-50 text-white transition-colors"
              :class="{ 'cursor-not-allowed': !results.get(selectedUuid)?.latex, 'cursor-pointer': results.get(selectedUuid)?.latex }"
            >
              Download
            </button>
          </div>

          <div>
            <input type="hidden" name="latex" v-for="latex of results.get(selectedUuid)?.latex?.entries()" :key="latex[0]" :value="latex[1]" />
          </div>
        </form>
      </div>
    </div>
  </main>
</template>
