import { defineStore } from 'pinia';
import { ref } from 'vue';

const MAX_UNDO_STACK = 100;
const FILE_TYPES = new Set(['image/jpeg', 'image/png']);
const urlCreator = window.URL || window.webkitURL;

function createEmptyImage(result) {
  result ??= {};
  const canvas = document.createElement('canvas');
  canvas.width = 100;
  canvas.height = 100;
  canvas.toBlob((blob) => {
    result.blob = blob;
    result.url = urlCreator.createObjectURL(blob);
  });
  return result;
}

const EMPTY_IMAGE = createEmptyImage({});

export const useProjectStore = defineStore('project', () => {
  const images = ref(new Map());
  const sketches = ref(new Map());
  const results = ref(new Map());
  const undoStacks = ref(new Map());
  const redoStacks = ref(new Map());
  const selectedUuid = ref();

  function selectFile(uuid) {
    selectedUuid.value = uuid;
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

  function updateImage(file, uuid) {
    readFile(file, function (url, blob) {
      images.value.set(uuid, { url, blob });
    });
  }

  function removeFile(uuid) {
    images.value.delete(uuid);
    results.value.delete(uuid);
    sketches.value.delete(uuid);
    undoStacks.value.delete(uuid);
    redoStacks.value.delete(uuid);
    if (selectedUuid.value === uuid) selectedUuid.value = null;
  }

  function emptyFile() {
    const url = urlCreator.createObjectURL(new Blob([new ArrayBuffer(0)]));
    let uuid = url.split('/').at(-1);
    while (images.value.has(uuid)) uuid += '_1';
    images.value.set(uuid, null);
    selectFile(uuid);
  }

  function clearImage(uuid) {
    images.value.set(uuid, null);
  }

  function saveSketch(blob, uuid) {
    const url = urlCreator.createObjectURL(blob);

    const undoStack = undoStacks.value.get(uuid) ?? [];
    const curSketch = sketches.value.get(uuid) ?? EMPTY_IMAGE;

    undoStack.push(curSketch);
    if (undoStack.length > MAX_UNDO_STACK) undoStack.splice(0, undoStack.length - MAX_UNDO_STACK);
    undoStacks.value.set(uuid, undoStack);
    redoStacks.value.set(uuid, []);

    sketches.value.set(uuid, { blob, url });
  }

  function undo(uuid) {
    const undoImage = undoStacks.value.get(uuid)?.pop();
    if (!undoImage) return;

    const curSketch = sketches.value.get(uuid);
    const redoStack = redoStacks.value.get(uuid) ?? [];

    if (curSketch) redoStack.push(curSketch);
    redoStacks.value.set(uuid, redoStack);
    sketches.value.set(uuid, undoImage);
  }

  function redo(uuid) {
    const redoImage = redoStacks.value.get(uuid)?.pop();
    if (!redoImage) return;

    const curSketch = sketches.value.get(uuid);
    const undoStack = undoStacks.value.get(uuid) ?? [];

    if (curSketch) undoStack.push(curSketch);
    undoStacks.value.set(uuid, undoStack);
    sketches.value.set(uuid, redoImage);
  }

  return {
    images,
    sketches,
    results,
    undoStacks,
    redoStacks,
    selectedUuid,
    selectFile,
    loadFile,
    loadFiles,
    updateImage,
    removeFile,
    emptyFile,
    clearImage,
    saveSketch,
    undo,
    redo,
  };
});
