<template>
    <div class="modal fade" ref="modalRef" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog" :class="modalClass">
            <div class="modal-content">
                <!-- Header -->
                <slot name="header">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <slot name="title">
                                {{ title }}
                            </slot>
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                </slot>
                <!-- Body -->
                <div class="modal-body">
                    <slot></slot>
                </div>
                <!-- Footer -->
                <div class="modal-footer">
                    <slot name="footer">
                        <button v-if="cancelText" type="button" :class="cancelClass" data-bs-dismiss="modal">{{ cancelText }}</button>
                        <button v-if="okText" type="button" :class="okClass" @click="ok" :disabled="okDisabled">{{ okText }}</button>
                    </slot>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { Modal } from 'bootstrap';

export default {
    name: 'BootstrapModal',
    props: {
        modelValue: Boolean, // For v-model support
        title: { type: String, default: 'Modal' },
        small: Boolean,
        large: Boolean,
        extraLarge: Boolean,
        scrollable: Boolean,
        force: Boolean, // Prevents closing on backdrop click or escape key
        okText: { type: String, default: 'OK' },
        cancelText: { type: String, default: 'Cancel' },
        okClass: { type: String, default: 'btn btn-primary' },
        cancelClass: { type: String, default: 'btn btn-secondary' },
        okDisabled: Boolean,
    },
    emits: ['update:modelValue', 'ok', 'shown', 'hidden'],
    data() {
        return {
            modalInstance: null,
        };
    },
    computed: {
        modalClass() {
            return {
                'modal-xl': this.extraLarge,
                'modal-lg': this.large,
                'modal-sm': this.small,
                'modal-dialog-scrollable': this.scrollable,
            };
        }
    },
    mounted() {
        if (!this.$refs.modalRef) return; // Safety check

        this.modalInstance = new Modal(this.$refs.modalRef, {
            backdrop: this.force ? 'static' : true,
            keyboard: !this.force,
        });

        // Relay Bootstrap's native 'shown' event to the parent
        this.$refs.modalRef.addEventListener('shown.bs.modal', () => {
            this.$emit('shown');

        });

        // Relay Bootstrap's native 'hidden' event to the parent
        this.$refs.modalRef.addEventListener('hidden.bs.modal', () => {
            // When Bootstrap hides the modal, ensure the v-model state is synced
            this.$emit('update:modelValue', false);
            this.$emit('hidden');
        });

        // If the modal should be shown initially, show it.
        if (this.modelValue) {
            this.modalInstance.show();
        }
    },
    beforeUnmount() {
        if (this.modalInstance) {
            // Dispose of the Bootstrap instance to prevent memory leaks
            this.modalInstance.dispose();
        }
    },
    watch: {
        modelValue(newValue) {
            if (this.modalInstance) {
                if (newValue) {
                    this.modalInstance.show();
                } else {
                    this.modalInstance.hide();
                }
            }
        }
    },
    methods: {
        ok() {
            // Emit the 'ok' event for the parent to handle.
            // The parent is responsible for closing the modal via v-model if needed.
            this.$emit('ok');

        }
    }
};
</script>