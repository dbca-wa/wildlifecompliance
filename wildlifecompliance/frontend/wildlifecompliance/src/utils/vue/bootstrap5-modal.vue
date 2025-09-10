<template>
    <div v-if="modelValue">
        <teleport to="body"><!-- Teleport to move the modal to the end of the body, which solves z-index issues.  -->
            <div
                class="modal fade"
                :class="{ show: isActive }"
                tabindex="-1"
                role="dialog"
                style="display: block"
                @click.self="$emit('update:modelValue', false)"
            >
                <div class="modal-dialog" :class="modalClass" role="document">
                    <div class="modal-content">
                        <slot name="header">
                            <div class="modal-header">
                                <h5 class="modal-title">
                                    <slot name="title">{{ title }}</slot>
                                </h5>
                                <button
                                    type="button"
                                    class="btn-close"
                                    aria-label="Close"
                                    @click="$emit('update:modelValue', false)"
                                ></button>
                            </div>
                        </slot>
                        <div class="modal-body">
                            <slot></slot>
                        </div>
                        <div v-if="!noFooter" class="modal-footer">
                            <slot name="footer">
                                <button
                                    type="button"
                                    class="btn btn-secondary"
                                    @click="$emit('close')"
                                >
                                    {{ cancelText }}
                                </button>
                                <button
                                    type="button"
                                    class="btn btn-primary"
                                    @click="$emit('submit')"
                                >
                                    {{ okText }}
                                </button>
                            </slot>
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-backdrop fade" :class="{ show: isActive }"></div>
        </teleport>
    </div>
</template>

<script>
export default {
    compatConfig: {
        COMPONENT_V_MODEL: false
    },
    props: {
        // v-model support for showing/hiding the modal
        modelValue: {
            type: Boolean,
            default: false,
        },
        title: {
            type: String,
            default: 'Modal',
        },
        size: {
            type: String,
            default: '', // 'sm', 'lg', 'xl'
        },
        okText: {
            type: String,
            default: 'OK',
        },
        cancelText: {
            type: String,
            default: 'Cancel',
        },
        noFooter: {
            type: Boolean,
            default: false,
        },
    },
    // Declare the events for v-model and other actions
    emits: ['update:modelValue', 'submit', 'close'],
    data() {
        return {
            isActive: false,
        };
    },
    computed: {
        modalClass() {
            if (this.size) {
                return `modal-${this.size}`;
            }
            return '';
        },
    },
    watch: {
        // Watch for the v-model value to change
        modelValue(newValue) {
            if (newValue) {
                // When showing, add class to body and activate modal
                document.body.classList.add('modal-open');
                // Use setTimeout to allow the fade-in animation to work
                setTimeout(() => {
                    this.isActive = true;
                }, 10);
            } else {
                // When hiding, deactivate first, then remove body class after animation
                this.isActive = false;
                setTimeout(() => {
                    document.body.classList.remove('modal-open');
                }, 300); // 300ms is a typical bootstrap animation duration
            }
        },
    },
};
</script>

<style scoped>
.modal.show {
    background-color: rgba(0, 0, 0, 0.5);
}
.modal {
    display: block;
}

.modal .btn {
    margin-bottom: 0px;
}

.modal-header {
    border-top-left-radius: 0.3rem;
    border-top-right-radius: 0.3rem;
    background-color: #efefef;
    color: #333333;
}

.btn-close {
    color: #333333;
    float: right;
}

.modal-footer {
    border-bottom-left-radius: 0.3rem;
    border-bottom-right-radius: 0.3rem;
}

.modal-body {
    background-color: #fff;
    color: #333333;
}

.modal-footer {
    background-color: #efefef;
    color: #333333;
}

.modal-transition {
    transition: all 0.6s ease;
}

.modal-leave {
    border-radius: 1px !important;
}

.modal-transition .modal-dialog,
.modal-transition .modal-backdrop {
    transition: all 0.5s ease;
}

.modal-enter .modal-dialog,
.modal-leave .modal-dialog {
    opacity: 0;
    transform: translateY(-30%);
}

.modal-enter .modal-backdrop,
.modal-leave .modal-backdrop {
    opacity: 0;
}

.close {
    font-size: 2.5rem;
    opacity: 0.3;
}

.close:hover {
    opacity: 0.7;
}

#okBtn {
    margin-bottom: 0px;
}
</style>