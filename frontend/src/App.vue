<script setup>
import { vElementSize } from '@vueuse/components';
import { ref, watch } from 'vue';
import UploadIcon from './components/UploadIcon.vue';
import PencilIcon from './components/PencilIcon.vue';
import EraserIcon from './components/EraserIcon.vue';
import TrashIcon from './components/TrashIcon.vue';
import ClearImageIcon from './components/ClearImageIcon.vue';
import AddImageIcon from './components/AddImageIcon.vue';
import LineIcon from './components/LineIcon.vue';
import RectangleIcon from './components/RectangleIcon.vue';
import OvalIcon from './components/OvalIcon.vue';
import DotIcon from './components/DotIcon.vue';
import CopyIcon from './components/CopyIcon.vue';

const urlCreator = window.URL || window.webkitURL;

const FILE_TYPES = new Set(['image/jpeg', 'image/png']);
const PEN_MODES = [
  { mode: 'draw', icon: PencilIcon },
  { mode: 'erase', icon: EraserIcon },
  { mode: 'line', icon: LineIcon },
  { mode: 'rectangle', icon: RectangleIcon },
  { mode: 'oval', icon: OvalIcon },
];
const PEN_SIZES = [2, 3, 5, 7, 9];
const CIRCLE = 2 * Math.PI;
const MATH_REGEX = /\\(begin|end)\{math\}/gi;

const btnFileUpload = ref('btnFileUpload');
const btnFileAdd = ref('btnFileAdd');
const spanCopy = ref('spanCopy');
const downloadForm = ref('downloadForm');
const canvas = ref('canvas');
const sketchCanvas = ref('sketchCanvas');

const fillMode = ref();
const penColour = ref('black');
const selectingColour = ref();
const draggedOver = ref();
const dragOverTimeout = ref();
const isAnalysing = ref();
const isDrawing = ref();

const images = ref(new Map());
const results = ref(new Map());
const sketches = ref(new Map());

const selectedUuid = ref();
const selectedMode = ref(PEN_MODES[0].mode);
const selectedSize = ref(PEN_SIZES[Math.floor((PEN_SIZES.length - 1) / 2)]);

let resizeDebounce;
let curX;
let curY;
let anchorX;
let anchorY;

function getCtx() {
  return canvas.value.getContext('2d');
}

function getCtxSketch() {
  return sketchCanvas.value.getContext('2d');
}

function readFile(file, callback) {
  if (!FILE_TYPES.has(file.type)) return;

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

    if (select) selectFile(uuid);
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
  sketches.value.delete(uuid);
}

function emptyImage() {
  const url = urlCreator.createObjectURL(new Blob([new ArrayBuffer(0)]));
  let uuid = url.split('/').at(-1);
  while (images.value.has(uuid)) uuid += '_1';
  images.value.set(uuid, null);
  selectFile(uuid);
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

watch(
  [selectedUuid, sketches],
  (newValue, oldValue) => {
    const ctx = getCtx();

    const sketch = sketches.value.get(newValue[0])?.url;
    if (!sketch) {
      canvasClear();
      return;
    } else if (oldValue[0] === newValue[0]) {
      return;
    }

    canvasClear();
    const img = new Image();
    img.onload = function () {
      ctx.drawImage(img, 0, 0);
    };
    img.src = sketch;
  },
  { deep: true },
);

function analyse(uuid) {
  if (isAnalysing.value) return;

  const fileImageUrl = images.value.get(uuid)?.url;

  const uploadImage = async function (image) {
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
  };

  const loadCanvasImage = function (canvasImage) {
    canvasImage.src = sketches.value.get(uuid)?.url;
  };

  const tempCanvas = document.createElement('canvas');
  tempCanvas.width = canvas.value.width;
  tempCanvas.height = canvas.value.height;
  const ctx = tempCanvas.getContext('2d');
  ctx.beginPath();
  ctx.fillStyle = 'white';
  ctx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);

  const fileImage = new Image();
  const canvasImage = new Image();
  fileImage.onload = function () {
    ctx.drawImage(fileImage, 0, 0);
    loadCanvasImage(canvasImage);
  };

  canvasImage.onload = function () {
    ctx.drawImage(canvasImage, 0, 0);
    tempCanvas.toBlob((blob) => uploadImage(blob));
  };

  if (fileImageUrl) fileImage.src = fileImageUrl;
  else loadCanvasImage(canvasImage);
}

function buildSvg(latex = []) {
  const html = [];

  for (const line of latex) {
    if (line === '\n') {
      html.push('<br/>');
    } else if (line.includes('\n')) {
      html.push(...buildSvg(line.split('\n')));
    } else if (line.match(/\\/gi)) {
      const text = line.replaceAll(MATH_REGEX, '').trim();
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

function onResize({ width, height }) {
  if (resizeDebounce) {
    clearTimeout(resizeDebounce);
    resizeDebounce = null;
  }

  resizeDebounce = setTimeout(() => {
    const oriWidth = canvas.value?.width;
    const oriHeight = canvas.value?.height;

    width = Math.floor(width);
    height = Math.floor(height);
    if (oriWidth === width && oriHeight === height) return;
    if (!width || !height) return;

    const ctx = getCtx();
    const scale = width / oriWidth;

    canvas.value.toBlob((blob) => {
      createImageBitmap(blob).then((imageBitmap) => {
        canvas.value.width = width;
        canvas.value.height = height;
        sketchCanvas.value.width = width;
        sketchCanvas.value.height = height;

        ctx.scale(scale, scale);
        ctx.drawImage(imageBitmap, 0, 0);
        ctx.setTransform(1, 0, 0, 1, 0, 0);

        resizeDebounce = null;
      });
    });
  }, 500);
}

function saveCanvas() {
  canvas.value.toBlob((blob) => {
    const url = urlCreator.createObjectURL(blob);
    sketches.value.set(selectedUuid.value, { blob, url });
  });
}

function canvasClear() {
  getCtx().clearRect(0, 0, canvas.value.width, canvas.value.height);
}

function sketchClear() {
  getCtxSketch().clearRect(0, 0, sketchCanvas.value.width, sketchCanvas.value.height);
}

function drawLine({ ctx, x, y, size, fromX, fromY, clear = false }) {
  if (fromX !== undefined && fromY !== undefined) ctx.moveTo(fromX, fromY);
  if (!clear) ctx.strokeStyle = penColour.value;

  ctx.lineTo(x, y);
  ctx.lineWidth = size;
  ctx.stroke();
}

function drawOval({ ctx, x, y, radiusX, radiusY, stroke = true, size, fill }) {
  ctx.beginPath();
  ctx.ellipse(x, y, radiusX, radiusY, 0, 0, CIRCLE);
  if (stroke) {
    ctx.lineWidth = size;
    ctx.strokeStyle = penColour.value;
    ctx.stroke();
  }
  if (fill) {
    ctx.fillStyle = penColour.value;
    ctx.fill();
  }
  ctx.closePath();
}

function drawRect({ ctx, x, y, width, height, stroke = true, size, fill }) {
  ctx.beginPath();
  ctx.rect(x, y, width, height);
  if (stroke) {
    ctx.lineWidth = size;
    ctx.strokeStyle = penColour.value;
    ctx.stroke();
  }
  if (fill) {
    ctx.fillStyle = penColour.value;
    ctx.fill();
  }
  ctx.closePath();
}

function clearRect({ ctx, x, y, size }) {
  ctx.clearRect(x, y, size, size);
}

function getLocation(event) {
  const location = canvas.value.getBoundingClientRect();
  curX = event.clientX - location.left;
  curY = event.clientY - location.top;
  return { curX, curY };
}

function canvasMouseDown(event) {
  if (!images.value.has(selectedUuid.value)) return;
  isDrawing.value = true;

  const { curX, curY } = getLocation(event);
  const size = selectedSize.value;
  const ctx = getCtx();
  ctx.globalCompositeOperation = 'source-over';

  switch (selectedMode.value) {
    case 'draw':
      drawRect({
        ctx,
        x: curX - size / 2,
        y: curY - size / 2,
        width: size,
        height: size,
        fill: true,
        stroke: false,
      });
      ctx.beginPath();
      ctx.moveTo(curX, curY);
      break;

    case 'erase':
      clearRect({ ctx, x: curX - size / 2, y: curY - size / 2, size });
      ctx.beginPath();
      ctx.globalCompositeOperation = 'destination-out';
      ctx.moveTo(curX, curY);
      break;

    case 'line':
    case 'rectangle':
    case 'oval':
      anchorX = curX;
      anchorY = curY;
      break;
  }
}

function canvasMouseEnd(event) {
  if (!isDrawing.value) return;

  const { curX: x, curY: y } = getLocation(event);
  const size = selectedSize.value;
  const ctx = getCtx();

  switch (selectedMode.value) {
    case 'draw':
      ctx.closePath();
      break;

    case 'line':
      if (anchorX === null || anchorY === null) break;
      sketchClear();
      ctx.beginPath();
      drawLine({ ctx, x, y, size, fromX: anchorX, fromY: anchorY });
      ctx.closePath();
      break;

    case 'rectangle':
      if (anchorX === null || anchorY === null) break;
      sketchClear();
      drawRect({
        ctx,
        x: Math.min(anchorX, x),
        y: Math.min(anchorY, y),
        width: Math.abs(x - anchorX),
        height: Math.abs(y - anchorY),
        size,
        fill: fillMode.value,
      });
      break;

    case 'oval':
      if (anchorX === null || anchorY === null) break;
      sketchClear();
      drawOval({
        ctx,
        x: (anchorX + x) / 2,
        y: (anchorY + y) / 2,
        radiusX: Math.abs(x - anchorX) / 2,
        radiusY: Math.abs(y - anchorY) / 2,
        size,
        fill: fillMode.value,
      });
      break;
  }

  ctx.globalCompositeOperation = 'source-over';
  anchorX = null;
  anchorY = null;

  isDrawing.value = false;
  saveCanvas();
}

function canvasMouseLeave() {
  if (!isDrawing.value) {
    sketchClear();
  }
}

function canvasMouseMove(event) {
  const { curX: x, curY: y } = getLocation(event);
  const size = selectedSize.value;
  const ctx = getCtx();
  const ctxSketch = getCtxSketch();

  if (!isDrawing.value) {
    sketchClear();
    drawRect({
      ctx: ctxSketch,
      x: curX - size / 2,
      y: curY - size / 2,
      width: size,
      height: size,
      fill: true,
      stroke: false,
    });
    return;
  }

  switch (selectedMode.value) {
    case 'draw':
      drawLine({ ctx, x, y, size });
      break;

    case 'erase':
      drawLine({ ctx, x, y, size, clear: true });
      break;

    case 'line':
      if (anchorX === null || anchorY === null) break;
      sketchClear();
      ctxSketch.beginPath();
      drawLine({ ctx: ctxSketch, x, y, size, fromX: anchorX, fromY: anchorY });
      ctxSketch.closePath();
      break;

    case 'rectangle':
      if (anchorX === null || anchorY === null) break;
      sketchClear();
      drawRect({
        ctx: ctxSketch,
        x: Math.min(anchorX, x),
        y: Math.min(anchorY, y),
        width: Math.abs(x - anchorX),
        height: Math.abs(y - anchorY),
        size,
        fill: fillMode.value,
      });
      break;

    case 'oval':
      if (anchorX === null || anchorY === null) break;
      sketchClear();
      drawOval({
        ctx: ctxSketch,
        x: (anchorX + x) / 2,
        y: (anchorY + y) / 2,
        radiusX: Math.abs(x - anchorX) / 2,
        radiusY: Math.abs(y - anchorY) / 2,
        size,
        fill: fillMode.value,
      });
      break;
  }
}
</script>

<template>
  <main
    @dragover.prevent="dragOver"
    @dragleave.prevent="dragEnd"
    @dragend.prevent="dragEnd"
    @drop.prevent="dropFiles"
    @mouseup.prevent="canvasMouseEnd"
    class="h-screen flex flex-col justify-center items-center bg-neutral-200"
  >
    <h1 class="mb-4 font-bold tracking-wider text-5xl">Math OCR</h1>

    <div class="h-[87%] w-[90%] grid grid-rows-[calc(var(--spacing)*30)_calc(var(--spacing))_1fr] bg-white border-cyan-800 border-4 rounded-t-xl">
      <div class="relative h-30 w-full px-0.5 overflow-x-auto overflow-y-hidden scroll-smooth text-nowrap horizontal-custom-scrollbar">
        <div v-for="item of images.entries()" :key="item[0]" class="relative h-full w-20 p-1 inline-block">
          <div @click="selectFile(item[0])" class="relative h-full w-full border-2 rounded-sm bg-gray-200 cursor-pointer hover:brightness-90 active:brightness-80 select-none">
            <img v-show="item[1]" :src="item[1]?.url" :alt="`img-${item[0]}`" class="h-full w-full rounded-sm object-contain object-left-top" />
            <img
              v-show="sketches.get(item[0])"
              :src="sketches.get(item[0])?.url"
              :alt="`img-${item[0]}`"
              class="absolute top-0 left-0 h-full w-full rounded-sm object-contain object-left-top"
            />
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
            v-for="mode of PEN_MODES"
            :key="mode.mode"
            @click="selectedMode = mode.mode"
            class="w-10 h-10 flex justify-center items-center cursor-pointer hover:brightness-90 active:brightness-80"
            :class="{ 'bg-slate-300': selectedMode === mode.mode, 'bg-white': selectedMode !== mode.mode }"
          >
            <component :is="mode.icon" width="30" height="30" />
          </button>

          <button
            @click="
              () => {
                canvasClear();
                saveCanvas();
              }
            "
            class="w-10 h-10 flex justify-center items-center cursor-pointer bg-white hover:brightness-90 active:brightness-80"
          >
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
            v-for="size of PEN_SIZES"
            :key="size"
            @click="selectedSize = size"
            class="w-10 h-10 flex justify-center items-center cursor-pointer hover:brightness-90 active:brightness-80"
            :class="{ 'bg-slate-300': selectedSize === size, 'bg-white': selectedSize !== size }"
          >
            <DotIcon :width="size" :height="size" />
          </button>

          <div class="flex flex-col justify-center items-center my-2">
            <label class="switch">
              <input id="fill-checkbox" @click="(event) => (fillMode = event.currentTarget.checked)" type="checkbox" />
              <span class="slider round"></span>
            </label>
            <label for="fill-checkbox">Fill</label>

            <label for="colour-selector"><div class="w-4 h-4 border-2" :style="{ background: fillMode ? penColour : 'transparent', 'border-color': penColour }"></div></label>
            <input
              type="color"
              id="colour-selector"
              class="w-0 h-0"
              @focus="selectingColour = true"
              @blur="selectingColour = false"
              @change="(event) => (penColour = event.currentTarget.value)"
            />
          </div>
        </div>

        <div class="relative h-full border-r-2 border-cyan-800">
          <div id="image-dropper" class="absolute top-1/8 left-1/8 h-3/4 w-3/4 m-auto border-4 border-gray-400 border-dashed"></div>

          <div v-show="!draggedOver" class="absolute w-full h-full p-1 pb-0 flex justify-center bg-white overflow-auto">
            <div class="relative w-full min-h-full h-fit pb-1">
              <img v-show="images.get(selectedUuid)?.url" :src="images.get(selectedUuid)?.url" class="w-full border-2 border-gray-400" />

              <div
                v-element-size="onResize"
                class="absolute top-0 z-10 w-full h-[calc(100%-var(--spacing))] border-2"
                :class="{ 'cursor-crosshair': images.has(selectedUuid) && !selectingColour }"
              >
                <canvas
                  ref="canvas"
                  @mousedown="canvasMouseDown"
                  @mouseup="canvasMouseEnd"
                  @mousemove="canvasMouseMove"
                  @mouseleave="canvasMouseLeave"
                  class="w-full h-full"
                  :class="{ 'pointer-events-none': selectingColour }"
                ></canvas>
                <canvas ref="sketchCanvas" class="absolute top-0 left-0 w-full h-full pointer-events-none"></canvas>
              </div>
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
