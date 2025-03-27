<script setup>
const props = defineProps(['width', 'height']);
</script>

<template>
  <svg :width="`${props.width ?? 50}px`" :height="`${props.height ?? 50}px`" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" fill="#000000">
    <g id="SVGRepo_bgCarrier" stroke-width="0"></g>
    <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round" stroke="#CCCCCC" stroke-width="1.44"></g>
    <g id="SVGRepo_iconCarrier">
      <title>70 Basic icons by Xicons.co</title>
      <rect x="1" y="2" width="46" height="45" rx="4" ry="4" fill="#38b1e7"></rect>
      <circle cx="32" cy="15" r="7" fill="#f9d74a"></circle>
      <path d="M35,31.13l-6.77,8.29L16.75,25a2,2,0,0,0-3.15,0L1.74,40.57A4,4,0,0,0,4.92,47H43.08a4,4,0,0,0,3-6.62l-8-9.29A2,2,0,0,0,35,31.13Z" fill="#826f57"></path>
    </g>
    <line x1="0" y1="0" x2="48" y2="48" style="stroke: #f44336; stroke-width: 5" />
    <line x1="0" y1="48" x2="48" y2="0" style="stroke: #f44336; stroke-width: 5" />
  </svg>
</template>

<script>
export default {
  name: 'ClearImageIcon',
  data() {
    return {};
  },
};
</script>
