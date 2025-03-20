<script setup>
import { storeToRefs } from 'pinia';
import { useProjectStore } from '@/stores/project';
import { defineProps, ref } from 'vue';
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

const spanCopy = ref();
const analysisType = ref();
const downloadForm = ref();

const isAnalysing = ref();

function copy(selected) {
  navigator.permissions.query({ name: 'clipboard-write' }).then((result) => {
    if (result.state === 'granted') {
      let text;
      if (analysisType.value.value === 'text_formula') {
        text = selected?.mathml.join('');
        if ((text.match(new RegExp('http://www.w3.org/1998/Math/MathML', 'g')) || []).length > 1) {
          text = text.split('<math xmlns="http://www.w3.org/1998/Math/MathML"').join('\n\n<math xmlns="http://www.w3.org/1998/Math/MathML"');
        }
      } else {
        text = selected?.latex.join('');
      }

      const blob = new Blob([text.trim()], { type: 'text/plain' });
      const item = new ClipboardItem({ 'text/plain': blob });

      navigator.clipboard.write([item]).then(
        () => {
          spanCopy.value.textContent = 'Copied!';
          setTimeout(() => (spanCopy.value.textContent = 'Copy'), 2000);
        },
        () => console.error('Unable to write to clipboard.'),
      );
    } else {
      spanCopy.value.textContent = 'No permission to copy!';
      setTimeout(() => (spanCopy.value.textContent = 'Copy'), 2000);
    }
  });
}

function download() {
  downloadForm.value.method = 'POST';
  downloadForm.value.action = DOWNLOAD_URL;
  downloadForm.value.target = '_blank';
  downloadForm.value.submit();
}

function buildSvg(latex = []) {
  const html = [];

  for (const line of latex) {
    if (line === '\n') {
      html.push('<br/>');
    } else if (line.includes('\n')) {
      html.push(...buildSvg(line.split('\n')));
    } else if (line.match(/\\/gi)) {
      const text = line.replaceAll(/\\(begin|end)\{math\}/gi, '').trim();
      if (text === '') continue;
      try {
        // MathJax is imported from index.html, ignore the eslint error
        // eslint-disable-next-line no-undef
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

function analyse(uuid) {
  if (isAnalysing.value) return;

  const fileImageUrl = images.value.get(uuid)?.url;
  const sketchesImageUrl = sketches.value.get(uuid)?.url;
  if (!(fileImageUrl || sketchesImageUrl)) return;

  const uploadImage = async function (image) {
    try {
      isAnalysing.value = true;
      const formData = new FormData();
      formData.append('file', image);
      formData.append('analysis_type', analysisType.value.value);
      formData.append('csrf_token', CSRF_TOKEN);

      const response = await fetch(ANALYSE_URL, { method: 'POST', body: formData });
      const body = await response.json();

      if (response.status === 200) {
        const output = body.output;
        const latex = output.latex;
        const omml = output.omml;
        const mathml = output.mathml;
        const html = buildSvg(latex);

        if (html[0] == '<br/>') html.shift(1);
        results.value.set(uuid, { html, latex, omml, mathml });
      } else if (response.status === 401) {
        window.location.href = LOGIN_URL
      } else if (body.error === 'Failed to analyse! Image too complex!') {
        const html = ['<div class="analysis-failed"><p>Analysis Failed!</p><p>The image is too complex!</p></div>'];
        results.value.set(uuid, { html });
      } else {
        throw new Error();
      }
    } catch {
      const html = ['<div class="analysis-failed"><p>Failed to connect to the server!</p><p>Please try again later!</p></div>'];
      results.value.set(uuid, { html });
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
    <div class="absolute h-[93.5%] w-full p-2 overflow-auto">
      <div v-for="html of results.get(selectedUuid)?.html?.entries()" :key="`latex-${html[0]}`" v-html="html[1]"></div>
    </div>

    <div class="absolute z-10 bottom-0 right-0 p-1 flex gap-2 font-bold font-[Consolas,monospace] border-t-2 border-l-2 select-none">
      <button
        @click.prevent="copy(results.get(selectedUuid))"
        v-show="results.get(selectedUuid)?.latex"
        :disabled="!results.get(selectedUuid)?.[analysisType.value === 'text_formula' ? 'mathml' : 'latex']"
        class="group px-3 py-1 flex items-center gap-1 border-1 border-[rgb(153,159,165)] bg-white enabled:hover:bg-[rgb(108,117,125)] enabled:active:bg-[rgb(85,92,100)] disabled:opacity-50 text-black hover:text-white active:text-white transition-colors"
        :class="results.get(selectedUuid)?.[analysisType.value === 'text_formula' ? 'mathml' : 'latex'] ? 'cursor-pointer' : 'cursor-not-allowed'"
      >
        <CopyIcon width="20" height="20" colour="black" class="group-hover:invert group-active:invert" />
        <span ref="spanCopy">Copy</span>
      </button>

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
        :disabled="isAnalysing || !(images.get(selectedUuid) || sketches.get(selectedUuid))"
        class="px-3 py-1 bg-[rgb(40,167,69)] enabled:hover:bg-[rgb(33,136,56)] enabled:active:bg-[rgb(30,126,52)] disabled:opacity-50 text-white transition-colors"
        :class="{ 'cursor-wait': isAnalysing, 'cursor-not-allowed': !selectedUuid, 'cursor-pointer': selectedUuid && !isAnalysing }"
      >
        Analyse
      </button>

      <select ref="analysisType" class="self-center py-[6px] text-sm border-2 border-black">
        <option value="text_formula">Formula & Text (Slow)</option>
        <option value="text">Text only</option>
        <option value="en_text">English Text</option>
        <option value="ms_text">Malay Text</option>
        <option value="ms_text">English & Malay Text</option>
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
