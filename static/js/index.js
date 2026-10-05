Vue.createApp({
    name: "App",
    components: {
        VForm: VeeValidate.Form,
        VField: VeeValidate.Field,
        ErrorMessage: VeeValidate.ErrorMessage,
    },
    data() {
        const opts = JSON.parse(
            document.getElementById("options-data").textContent
        );
        return {
            options: opts,
            cakes: JSON.parse(document.getElementById("cakes-data").textContent),
            Auth: JSON.parse(document.getElementById("auth-data").textContent),
            NeedReg: false,
            Cake: null,
            schema1: {
                lvls: (value) => {
                    if (value) {
                        return true;
                    }
                    return ' количество уровней';
                },
                form: (value) => {
                    if (value) {
                        return true;
                    }
                    return ' форму торта';
                },
                topping: (value) => {
                    if (value) {
                        return true;
                    }
                    return ' топпинг';
                }
            },
            schema2: {
                name: (value) => {
                    if (value) {
                        return true;
                    }
                    return ' имя';
                },
                phone: (value) => {
                    if (value) {
                        return true;
                    }
                    return ' телефон';
                },
                name_format: (value) => {
                    const regex = /^[a-zA-Zа-яА-Я]+$/
                    if (!value) {
                        return true;
                    }
                    if ( !regex.test(value)) {

                        return 'Формат имени нарушен';
                    }
                    return true;
                },
                email_format: (value) => {
                    const regex = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i
                    if (!value) {
                        return true;
                    }
                    if ( !regex.test(value)) {

                        return 'Формат почты нарушен';
                    }
                    return true;
                },
                phone_format:(value) => {
                    const regex = /^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$/
                    if (!value) {
                        return true;
                    }
                    if ( !regex.test(value)) {

                        return 'Формат телефона нарушен';
                    }
                    return true;
                },
                email: (value) => {
                    if (value) {
                        return true;
                    }
                    return ' почту';
                },
                address: (value) => {
                    if (value) {
                        return true;
                    }
                    return ' адрес';
                },
                date: (value) => {
                    if (value) {
                        return true;
                    }
                    return ' дату доставки';
                },
                time: (value) => {
                    if (value) {
                        return true;
                    }
                    return ' время доставки';
                }
            },
            DATA: {
                Levels: ['не выбрано', ...opts.levels.map((o) => o.name)],
                Forms: ['не выбрано', ...opts.forms.map((o) => o.name)],
                Toppings: ['не выбрано', ...opts.toppings.map((o) => o.name)],
                Berries: ['нет', ...opts.berries.map((o) => o.name)],
                Decors: ['нет', ...opts.decors.map((o) => o.name)],
            },
            Costs: {
                Levels: [0, ...opts.levels.map((o) => o.price)],
                Forms: [0, ...opts.forms.map((o) => o.price)],
                Toppings: [0, ...opts.toppings.map((o) => o.price)],
                Berries: [0, ...opts.berries.map((o) => o.price)],
                Decors: [0, ...opts.decors.map((o) => o.price)],
                Words: 500
            },
            Levels: 0,
            Form: 0,
            Topping: 0,
            Berries: 0,
            Decor: 0,
            Words: '',
            Comments: '',
            Designed: false,

            Name: '',
            Phone: null,
            Email: null,
            Address: null,
            Dates: null,
            Time: null,
            DelivComments: ''
        }
    },
    methods: {
        Buy(pk) {
            this.Cake = pk;
            this.ToStep4('buy')
        },
        Unpick() {
            this.Cake = null;
            this.Designed = false;
            this.Levels = 0;
            this.Form = 0;
            this.Topping = 0;
            this.Berries = 0;
            this.Decor = 0;
            this.Words = '';
            this.Comments = '';
            window.scrollTo(0, 0)
        },
        ToStep4(from) {
            if (!this.Auth) {
                this.NeedReg = from
                return
            }
            this.Designed = true
            setTimeout(() => this.$refs.ToStep4.click(), 0);
        }
    },
    computed: {
        BaseCost() {
            const cake = this.cakes.find((c) => c.pk == this.Cake);
            if (cake) {
                return cake.price;
            }
            let W = this.Words ? this.Costs.Words : 0;
            return this.Costs.Levels[this.Levels] + this.Costs.Forms[this.Form] +
                this.Costs.Toppings[this.Topping] + this.Costs.Berries[this.Berries] +
                this.Costs.Decors[this.Decor] + W;
        },

        IsUrgent() {
            if (!this.Dates || !this.Time) {
            return false;
            }

            const delivery = new Date(this.Dates + "T" + this.Time);
            const now = new Date();

            const hoursLeft = (delivery - now) / (1000 * 60 * 60);

            return hoursLeft < 24;
        },

        UrgentSurcharge() {
            if (this.IsUrgent) {
                return Math.round(this.BaseCost * 0.2);
            }
            return 0;
        },

        Cost() {
            return this.BaseCost + this.UrgentSurcharge;
        }
    }
}).mount('#VueApp')