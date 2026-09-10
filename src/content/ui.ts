import type { LocalizedText } from "@/lib/i18n";

/**
 * Every piece of interface text on the site, in both languages.
 *
 * Business information does NOT belong here — that lives in site.ts,
 * services.ts, projects.ts, reviews.ts and faq.ts. This file is for labels,
 * buttons, headings and form copy.
 *
 * To change wording, edit the `uk` (Ukrainian) or `en` (English) value.
 */
export const ui = {
  nav: {
    services: { uk: "Послуги", en: "Services" },
    portfolio: { uk: "Портфоліо", en: "Portfolio" },
    about: { uk: "Студія", en: "Studio" },
    contact: { uk: "Контакти", en: "Contact" },
    menuOpen: { uk: "Відкрити меню", en: "Open menu" },
    menuClose: { uk: "Закрити меню", en: "Close menu" },
    skipToContent: { uk: "Перейти до вмісту", en: "Skip to content" },
    languageSwitcher: { uk: "Мова сайту", en: "Site language" },
    home: { uk: "Головна", en: "Home" },
  },

  actions: {
    book: { uk: "Записатися", en: "Book now" },
    viewPortfolio: { uk: "Дивитися роботи", en: "View portfolio" },
    viewService: { uk: "Детальніше", en: "Learn more" },
    viewProject: { uk: "Дивитися проєкт", en: "View project" },
    allServices: { uk: "Усі послуги", en: "All services" },
    allProjects: { uk: "Усі проєкти", en: "All projects" },
    call: { uk: "Зателефонувати", en: "Call us" },
    write: { uk: "Написати", en: "Message us" },
    backToPortfolio: { uk: "Назад до портфоліо", en: "Back to portfolio" },
    backToServices: { uk: "Назад до послуг", en: "Back to services" },
    backHome: { uk: "На головну", en: "Back to home" },
    close: { uk: "Закрити", en: "Close" },
  },

  labels: {
    duration: { uk: "Тривалість", en: "Duration" },
    price: { uk: "Вартість", en: "Price" },
    priceOnRequest: { uk: "Ціна за запитом", en: "Contact for price" },
    included: { uk: "Що входить", en: "What's included" },
    benefits: { uk: "Переваги", en: "Benefits" },
    servicesPerformed: { uk: "Виконані роботи", en: "Services performed" },
    vehicle: { uk: "Автомобіль", en: "Vehicle" },
    year: { uk: "Рік", en: "Year" },
    before: { uk: "До", en: "Before" },
    after: { uk: "Після", en: "After" },
    dragToCompare: { uk: "Потягніть, щоб порівняти", en: "Drag to compare" },
    openingHours: { uk: "Графік роботи", en: "Opening hours" },
    address: { uk: "Адреса", en: "Address" },
    phone: { uk: "Телефон", en: "Phone" },
    email: { uk: "Пошта", en: "Email" },
    follow: { uk: "Ми в соцмережах", en: "Follow us" },
    relatedServices: { uk: "Схожі послуги", en: "Related services" },
    moreProjects: { uk: "Інші проєкти", en: "More projects" },
    filterAll: { uk: "Усі роботи", en: "All work" },
  },

  sections: {
    servicesEyebrow: { uk: "Послуги", en: "Services" },
    servicesTitle: { uk: "Що ми робимо", en: "What we do" },
    portfolioEyebrow: { uk: "Портфоліо", en: "Portfolio" },
    portfolioTitle: { uk: "Вибрані проєкти", en: "Selected projects" },
    beforeAfterEyebrow: { uk: "До і після", en: "Before / After" },
    beforeAfterTitle: { uk: "Результат, який видно", en: "The difference you can see" },
    whyEyebrow: { uk: "Чому THE BOX", en: "Why THE BOX" },
    whyTitle: { uk: "Як ми працюємо", en: "How we work" },
    processEyebrow: { uk: "Процес", en: "Process" },
    processTitle: { uk: "Від запису до видачі", en: "From booking to handover" },
    materialsEyebrow: { uk: "Матеріали", en: "Materials" },
    materialsTitle: { uk: "Матеріали та обладнання", en: "Materials and equipment" },
    reviewsEyebrow: { uk: "Відгуки", en: "Reviews" },
    reviewsTitle: { uk: "Що кажуть клієнти", en: "What clients say" },
    instagramEyebrow: { uk: "Instagram", en: "Instagram" },
    instagramTitle: { uk: "Щоденна робота студії", en: "The studio, day to day" },
    faqEyebrow: { uk: "Питання", en: "Questions" },
    faqTitle: { uk: "Часті запитання", en: "Frequently asked" },
    contactEyebrow: { uk: "Контакти", en: "Contact" },
    contactTitle: { uk: "Записатися до студії", en: "Book your car in" },
  },

  form: {
    heading: { uk: "Залишити заявку", en: "Request a booking" },
    name: { uk: "Ім'я", en: "Name" },
    namePlaceholder: { uk: "Ваше ім'я", en: "Your name" },
    phone: { uk: "Телефон", en: "Phone" },
    email: { uk: "Email", en: "Email" },
    emailOptional: { uk: "Email (необов'язково)", en: "Email (optional)" },
    vehicle: { uk: "Автомобіль", en: "Vehicle" },
    make: { uk: "Марка", en: "Make" },
    model: { uk: "Модель", en: "Model" },
    carYear: { uk: "Рік", en: "Year" },
    service: { uk: "Послуга", en: "Service" },
    servicePlaceholder: { uk: "Оберіть послугу", en: "Select a service" },
    serviceUnsure: { uk: "Ще не визначився — порадьте", en: "Not sure yet — advise me" },
    date: { uk: "Бажана дата", en: "Preferred date" },
    dateHint: { uk: "Точний час узгодимо по телефону.", en: "We confirm the exact slot by phone." },
    message: { uk: "Повідомлення", en: "Message" },
    messageHint: {
      uk: "Стан авто, попередні роботи — все, що варто знати.",
      en: "Condition, previous work, anything we should know.",
    },
    messagePlaceholder: {
      uk: "Опишіть, що потрібно зробити",
      en: "Tell us what the car needs",
    },
    submit: { uk: "Надіслати заявку", en: "Send request" },
    submitting: { uk: "Надсилаємо…", en: "Sending…" },
    sendVia: { uk: "Або напишіть нам одразу:", en: "Or message us directly:" },
    successTitle: { uk: "Заявку сформовано", en: "Request ready" },
    successBody: {
      uk: "Ми відкрили месенджер із готовим повідомленням — надішліть його, і ми відповімо найближчим часом.",
      en: "We have opened your messenger with the request filled in — send it and we will reply shortly.",
    },
    successAgain: { uk: "Створити нову заявку", en: "Start another request" },
    required: { uk: "Обов'язкове поле", en: "Required" },
    errors: {
      name: { uk: "Вкажіть, будь ласка, ваше ім'я.", en: "Please enter your name." },
      phone: { uk: "Вкажіть номер телефону для зв'язку.", en: "Enter a phone number we can reach you on." },
      email: { uk: "Перевірте адресу електронної пошти.", en: "Enter a valid email address." },
      make: { uk: "Вкажіть марку.", en: "Required." },
      model: { uk: "Вкажіть модель.", en: "Required." },
      service: { uk: "Оберіть послугу.", en: "Please choose a service." },
    },
  },

  empty: {
    services: {
      uk: "Перелік послуг зараз оновлюється.",
      en: "The service list is being updated.",
    },
    projects: {
      uk: "Роботи скоро з'являться тут.",
      en: "Projects will appear here shortly.",
    },
    reviews: { uk: "Відгуки скоро з'являться.", en: "Reviews coming soon." },
  },

  notFound: {
    eyebrow: { uk: "Помилка 404", en: "Error 404" },
    title: { uk: "Такої сторінки немає", en: "This page does not exist" },
    body: {
      uk: "Схоже, адресу введено з помилкою або сторінку було переміщено.",
      en: "The address you followed does not match anything here.",
    },
  },

  footer: {
    rights: { uk: "Усі права захищено.", en: "All rights reserved." },
  },
} satisfies Record<string, unknown>;

/** Convenience type for anything that accepts a localized string from `ui`. */
export type UiText = LocalizedText;
