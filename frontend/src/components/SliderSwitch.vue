<template>
  <label class="switch">
    <input id="fill-checkbox" @click="(event) => $emit('triggered', event)" type="checkbox" />
    <span class="slider round"></span>
  </label>
</template>

<script>
export default {
  name: 'SliderSwitch',
  data() {
    return {};
  },
};
</script>
