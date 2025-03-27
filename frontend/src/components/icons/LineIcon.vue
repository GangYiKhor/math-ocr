<script setup>
const props = defineProps(['width', 'height']);
</script>

<template>
  <svg :width="`${props.width ?? 50}px`" :height="`${props.height ?? 50}px`" viewBox="0 0 512 512">
    <line x1="0" y1="512" x2="512" y2="0" style="stroke: black; stroke-width: 50" />
  </svg>
</template>

<script>
export default {
  name: 'LineIcon',
  data() {
    return {};
  },
};
</script>
