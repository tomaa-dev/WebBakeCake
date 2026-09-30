Vue.createApp({
    name: "RegApp",
    components: {
        VForm: VeeValidate.Form,
        VField: VeeValidate.Field,
        ErrorMessage: VeeValidate.ErrorMessage,
    },
    data() {
        return {
            RegSchema: {
                reg: (value) => {
                    if (value) {
                        return true;
                    }
                    return 'Поле не заполнено';
                },
                agree: (value) => {
                    if (value) {
                        return true;
                    }
                    return 'Без согласия на обработку персональных данных продолжить нельзя';
                },
                phone_format: (value) => {
                    const regex = /^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$/
                    if (!value) {
                        return true;
                    }
                    if ( !regex.test(value)) {

                        return '⚠ Формат телефона нарушен';
                    }
                    return true;
                },
                code_format: (value) => {
                    const regex = /^[a-zA-Z0-9]+$/
                    if (!value) {
                        return true;
                    }
                    if ( !regex.test(value)) {

                        return '⚠ Формат кода нарушен';
                    }
                    return true;
                }
            },
            Step: 'Number',
            RegInput: '',
            EnteredNumber: '',
            Agree: false
        }
    },
    mounted() {
        const el = this.$el
        if (el.dataset.initStep === 'Code') {
            this.Step = 'Code'
            this.EnteredNumber = el.dataset.initPhone || ''
        }
        if (el.dataset.initOpen === 'true') {
            this.OpenModal()
        }
    },
    methods: {
        OpenModal() {
            const modal = document.getElementById('RegModal')
            if (!modal) {
                return
            }
            if (window.bootstrap && window.bootstrap.Modal) {
                window.bootstrap.Modal.getOrCreateInstance(modal).show()
                return
            }
            const trigger = document.createElement('a')
            trigger.href = '#RegModal'
            trigger.dataset.bsToggle = 'modal'
            document.body.appendChild(trigger)
            trigger.click()
            trigger.remove()
        },
        RegSubmit() {
            this.$refs.HiddenFormSubmitReg.click()
        },
        ToRegStep1() {
            this.Step = 'Number'
            this.RegInput = this.EnteredNumber
        },
        Reset() {
            this.Step = 'Number'
            this.RegInput = ''
            this.EnteredNumber = ''
            this.Agree = false
        }
    }
}).mount('#RegModal')
