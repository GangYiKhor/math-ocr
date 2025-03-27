<script setup>
import { ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useProjectStore } from '@/stores/project';
import { useCanvasStore } from '@/stores/canvas';
import FileList from './components/FileList.vue';
import DownloadForm from './components/DownloadForm.vue';
import CanvasBoard from './components/CanvasBoard.vue';
import PenSelectors from './components/PenSelectors.vue';

const ANALYSE_URL = document.getElementById('analyse_url')?.value
const DOWNLOAD_URL = document.getElementById('download_url')?.value
const LOGIN_URL = document.getElementById('login_url')?.value
const CSRF_URL = document.getElementById('csrf_url')?.value
const CSRF_TOKEN = document.getElementById('csrf_token')?.value

function throttle(func, limit) {
  let inThrottle;
  return function() {
    if (!inThrottle) {
      func(arguments);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  }
}

const projectStore = useProjectStore();
const {
  images,
  sketches,
  undoStacks,
  redoStacks,
  selectedUuid
} = storeToRefs(projectStore);
const { addImage, loadFiles, selectFile } = projectStore;

const canvasStore = useCanvasStore();
const { isDrawing } = storeToRefs(canvasStore)
const { sethideCanvas } = canvasStore;

const MAX_FILE_SIZE = 50;
const canvasComponent = ref();

const draggedOver = ref();
const dragOverTimeout = ref();

function dragOver() {
  clearTimeout(dragOverTimeout.value);
  draggedOver.value = true;
  sethideCanvas(true);
  if (isDrawing.value) {
    // If dragged the page due to selection problem
    isDrawing.value = false;
    canvasComponent.value.resetCanvas()
  }
}

function dragEnd() {
  dragOverTimeout.value = setTimeout(() => {
    draggedOver.value = false;
    sethideCanvas(false);
  }, 100);
}

function dropFiles(event) {
  draggedOver.value = false;
  sethideCanvas(false);
  fixSelectBug();
  if (event.target.id !== 'image-dropper' || event.dataTransfer.files.length === 0) return;
  loadFiles(event.dataTransfer.files);
}

function fixSelectBug() {
  if (window.getSelection) {
    if (window.getSelection().empty) {
      // Chrome
      window.getSelection().empty();
    } else if (window.getSelection().removeAllRanges) {
      // Firefox
      window.getSelection().removeAllRanges();
    }
  } else if (document.selection) {
    // IE
    document.selection.empty();
  }
}

const checkLoginStatus = throttle(async function () {
  const response = await fetch(CSRF_URL);
    if (response.status === 401) {
      window.location.href = LOGIN_URL;
    }
}, 5 * 60 * 1000)

watch(
  [images, sketches],
  async () => checkLoginStatus(),
  { deep: true },
);

function onClearCanvas() {
  canvasComponent.value.canvasClear();
  canvasComponent.value.saveCanvas();
}

function undo() {
  const undoImage = undoStacks.value.get(selectedUuid.value)?.pop();
  if (!undoImage) return;

  const curSketch = sketches.value.get(selectedUuid.value);
  const redoStack = redoStacks.value.get(selectedUuid.value) ?? [];

  if (curSketch) redoStack.push(curSketch);
  redoStacks.value.set(selectedUuid.value, redoStack);
  sketches.value.set(selectedUuid.value, undoImage);

  canvasComponent.value.loadImage(undoImage.url);
}

function redo() {
  const redoImage = redoStacks.value.get(selectedUuid.value)?.pop();
  if (!redoImage) return;

  const curSketch = sketches.value.get(selectedUuid.value);
  const undoStack = undoStacks.value.get(selectedUuid.value) ?? [];

  if (curSketch) undoStack.push(curSketch);
  undoStacks.value.set(selectedUuid.value, undoStack);
  sketches.value.set(selectedUuid.value, redoImage);

  canvasComponent.value.loadImage(redoImage.url);
}

function mouseUp(event) {
  canvasComponent.value.canvasMouseEnd(event);
}

function keyDown(event) {
  if (event.key === 'z' && event.ctrlKey) undo()
  else if ((event.key ==='y' && event.ctrlKey) || (event.key === 'Z' && event.ctrlKey)) redo()
}

document.removeEventListener("keydown", keyDown);
document.addEventListener('keydown', keyDown);

async function loadClipboardImage() {
  const clipboardItems = await navigator.clipboard.read();

  let lastUuid;
  for (const clipboardItem of clipboardItems) {
    const imageTypes = clipboardItem.types?.filter(type => type.startsWith("image/"));

    for (const imageType of imageTypes) {
      const blob = await clipboardItem.getType(imageType);
      lastUuid = addImage({ blob });
    }
  }

  if (lastUuid) selectFile(lastUuid);
}

document.removeEventListener("paste", loadClipboardImage);
document.addEventListener("paste", loadClipboardImage);
</script>

<template>
  <main
    @dragover.prevent="dragOver"
    @dragleave.prevent="dragEnd"
    @dragend.prevent="dragEnd"
    @drop.prevent="dropFiles"
    @mouseup.prevent="mouseUp"
    class="h-screen flex flex-col justify-center items-center bg-neutral-200"
  >
    <h1 class="mb-4 font-bold tracking-wider text-5xl pointer-events-none select-none">Math OCR</h1>

    <div class="h-[87%] w-[85%] grid grid-rows-[calc(var(--spacing)*30)_calc(var(--spacing))_1fr] bg-white border-cyan-800 border-4 rounded-t-xl">
      <FileList :MAX_FILE_SIZE="MAX_FILE_SIZE" />

      <hr class="border-2 border-cyan-800" />

      <div class="relative flex-1 h-full grid grid-cols-2 grid-rows-1">
        <PenSelectors @onClearCanvas="onClearCanvas" @undo="undo" @redo="redo" />

        <div class="relative h-full border-r-2 border-cyan-800 select-none">
          <div id="image-dropper" class="absolute top-1/8 left-1/8 h-3/4 w-3/4 m-auto border-4 border-gray-400 border-dashed"></div>
          <CanvasBoard ref="canvasComponent"/>
        </div>

        <DownloadForm
          :DOWNLOAD_URL="DOWNLOAD_URL"
          :CSRF_TOKEN="CSRF_TOKEN"
          :ANALYSE_URL="ANALYSE_URL"
          :LOGIN_URL="LOGIN_URL"
        />
      </div>
    </div>
  </main>
</template>
