<script setup>
import { storeToRefs } from 'pinia';
import { useProjectStore } from '@/stores/project';
import { ref } from 'vue';
import { useCanvasStore } from '@/stores/canvas';
import CopyIcon from './icons/CopyIcon.vue';

const props = defineProps(['DOWNLOAD_URL', 'CSRF_TOKEN', 'ANALYSE_URL', 'LOGIN_URL']);
const DOWNLOAD_URL = props.DOWNLOAD_URL
const CSRF_TOKEN = props.CSRF_TOKEN
const ANALYSE_URL = props.ANALYSE_URL
const LOGIN_URL = props.LOGIN_URL

const project = useProjectStore();
const { images, sketches, results, selectedUuid } = storeToRefs(project);

const canvas = useCanvasStore();
const { canvasSize } = storeToRefs(canvas)
const { canvasLoadImage } = canvas;

const analysisType = ref();
const downloadForm = ref();

const isAnalysing = ref();
const controller = ref();

function copy(text, copiedSpan) {
  if (!text) return;

  navigator.permissions.query({ name: 'clipboard-write' }).then((result) => {
    if (result.state === 'granted') {
      navigator.clipboard.writeText(text);
      copiedSpan.textContent = 'Copied!';
      copiedSpan.style.color = '#008236';
      copiedSpan.style.opacity = 1;
      setTimeout(() => copiedSpan.style.opacity = 0, 1500)
    }
    else {
      copiedSpan.textContent = 'No permission to copy!';
      copiedSpan.style.color = '#e7000b';
      copiedSpan.style.opacity = 1;
      setTimeout(() => copiedSpan.style.opacity = 0, 1500)
    }
  });
}

function download() {
  downloadForm.value.method = 'POST';
  downloadForm.value.action = DOWNLOAD_URL;
  downloadForm.value.target = '_blank';
  downloadForm.value.submit();
}

function buildSvg(latex = [], mathml = []) {
  const formulas = [];

  for (const [index, line] of latex.entries()) {
    if (line.match(/\\/g)) {
      const text = line.replaceAll(/\\(begin|end)\{math\}/gi, '').trim();
      if (text === '') continue;
      try {
        formulas.push({
          // MathJax is imported from index.html, ignore the eslint error
          // eslint-disable-next-line no-undef
          html: MathJax.tex2svg(text).outerHTML,
          copy: mathml[index],
        })
      }
      catch {
        // If fail, skip it}
      }
    } else {
      formulas.push({
        html: `<span>${line.trim()}</span>`,
        copy: line,
      })
    }
  }

  return formulas;
}

function analyse(uuid) {
  if (isAnalysing.value) {
    controller.value?.abort('Cancelled by user');
    return;
  }

  const fileImageUrl = images.value.get(uuid)?.url;
  const sketchesImageUrl = sketches.value.get(uuid)?.url;
  if (!(fileImageUrl || sketchesImageUrl)) return;

  const uploadImage = async function (image) {
    try {
      const abortController = new AbortController();
      const signal = abortController.signal;

      isAnalysing.value = true;
      controller.value = abortController;

      const formData = new FormData();
      formData.append('file', image);
      formData.append('analysis_type', analysisType.value.value);
      formData.append('csrf_token', CSRF_TOKEN);

      const response = await fetch(ANALYSE_URL, { method: 'POST', body: formData, signal });
      const body = await response.json();

      if (response.status === 200) {
        const output = body.output;
        const latex = output.latex;
        const omml = output.omml;
        const mathml = output.mathml;
        const formulas = buildSvg(latex, mathml);

        results.value.set(uuid, { formulas, latex, omml, mathml });
      } else if (response.status === 401) {
        window.location.href = LOGIN_URL
      } else if (body.error === 'Failed to analyse! Image too complex!') {
        const html = ['<div class="analysis-failed"><p>Analysis Failed!</p><p>The image is too complex!</p></div>'];
        results.value.set(uuid, { formulas: [{ html }] });
      } else {
        throw new Error();
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        const html = ['<div class="analysis-failed"><p>Failed to connect to the server!</p><p>Please try again later!</p></div>'];
        results.value.set(uuid, { formulas: [{ html }] });
      }
    } finally {
      isAnalysing.value = false;
    }
  };

  const tempCanvas = document.createElement('canvas');
  tempCanvas.width = canvasSize.value.width;
  tempCanvas.height = canvasSize.value.height;
  const ctx = tempCanvas.getContext('2d');
  ctx.beginPath();
  ctx.fillStyle = 'white';
  ctx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);

  const getBlob = function () {
    tempCanvas.toBlob((blob) => uploadImage(blob));
  };

  if (fileImageUrl) {
    canvasLoadImage({
      ctx,
      url: fileImageUrl,
      width: tempCanvas.width,
      height: tempCanvas.height,
      cb: () =>
        canvasLoadImage({
          ctx,
          url: sketchesImageUrl,
          cb: getBlob,
        }),
    });
  } else {
    canvasLoadImage({ ctx, url: sketchesImageUrl, width: tempCanvas.width, height: tempCanvas.height, cb: getBlob });
  }
}
</script>

<template>
  <form ref="downloadForm" class="relative h-full border-l-2 border-cyan-800">
    <div class="absolute h-[calc(100%-73.5px)] w-full p-2 overflow-auto">
      <div v-for="formula of results.get(selectedUuid)?.formulas?.entries()" :key="`result-${formula[0]}`">
        <div v-if="formula[1]?.copy === undefined" v-html="formula[1]?.html">
        </div>

        <button
          v-if="formula[1]?.copy"
          @click.prevent.stop="(e) => copy(formula[1]?.copy, e.currentTarget.querySelector('.copied-text'))"
          class="formula-copy px-2 w-full flex justify-between items-center hover:bg-gray-200 active:bg-gray-300 transition-colors cursor-pointer"
        >
          <div v-html="formula[1]?.html"></div>
          <div class="relative">
            <span class="copied-text absolute right-7 bottom-0 font-bold text-red-600 text-nowrap">Copied!</span>
            <CopyIcon width="20" height="20" colour="black" />
          </div>
        </button>
      </div>
    </div>

    <div class="absolute z-10 bottom-0 right-0 p-1 w-full flex justify-end gap-2 font-bold font-[Consolas,monospace] border-t-2 select-none">
      <button
        @click.prevent="download(results.get(selectedUuid)?.latex)"
        v-show="results.get(selectedUuid)?.latex"
        :disabled="!results.get(selectedUuid)?.latex"
        ref="btnDownload"
        class="px-3 py-1 bg-[rgb(23,162,184)] enabled:hover:bg-[rgb(19,132,150)] enabled:active:bg-[rgb(17,122,139)] disabled:opacity-50 text-white transition-colors"
        :class="results.get(selectedUuid)?.latex ? 'cursor-pointer' : 'cursor-not-allowed'"
      >
        Download
      </button>

      <button
        @click.prevent="analyse(selectedUuid)"
        :disabled="!isAnalysing && !selectedUuid"
        class="px-3 py-1 disabled:opacity-50 bg-[rgb(40,167,69)] hover:bg-[rgb(33,136,56)] active:bg-[rgb(30,126,52)] text-white transition-colors"
        :class="{
          'saturate-10 cursor-progress': isAnalysing,
          'cursor-pointer': selectedUuid && !isAnalysing,
        }"
      >
        {{ isAnalysing ? 'Cancel' : 'Analyse' }}
      </button>

      <select ref="analysisType" class="self-center py-[6px] text-sm border-2 border-black">
        <option value="text_formula">Formula (Slow)</option>
        <option value="en_ms_text">Text</option>
      </select>
    </div>

    <div>
      <input type="hidden" name="csrf_token" :value="CSRF_TOKEN"/>
      <input type="hidden" name="latex" v-for="latex of results.get(selectedUuid)?.latex?.entries()" :key="latex[0]" :value="latex[1]" />
    </div>
  </form>
</template>

<script>
export default {
  name: 'DownloadForm',
  data() {
    return {};
  },
};
</script>
