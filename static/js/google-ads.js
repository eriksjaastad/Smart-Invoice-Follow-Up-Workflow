(function initSmartInvoiceAds(window, document) {
    const CONVERSION_ID = "AW-18081954084";
    const CONVERSION_LABELS = {
        lead: "gJ-bCK_ukZscEKTykq5D",
        checkoutStart: "DlJ1CJbHw6AcEKTykq5D",
        purchase: "Am4KCOev16AcEKTykq5D",
    };
    const STORAGE_PREFIX = "smart-invoice-ads:";

    function ensureGoogleTagLoaded() {
        if (document.querySelector(`script[data-google-ads-tag="${CONVERSION_ID}"]`)) {
            return;
        }

        const script = document.createElement("script");
        script.async = true;
        script.src = `https://www.googletagmanager.com/gtag/js?id=${CONVERSION_ID}`;
        script.dataset.googleAdsTag = CONVERSION_ID;
        document.head.appendChild(script);
    }

    function getStorageKey(key) {
        return `${STORAGE_PREFIX}${key}`;
    }

    function hasSessionStorage() {
        try {
            return typeof window.sessionStorage !== "undefined";
        } catch (error) {
            return false;
        }
    }

    function hasTracked(key) {
        if (!hasSessionStorage()) {
            return false;
        }

        return window.sessionStorage.getItem(getStorageKey(key)) === "1";
    }

    function markTracked(key) {
        if (!hasSessionStorage()) {
            return;
        }

        window.sessionStorage.setItem(getStorageKey(key), "1");
    }

    function trackOnce(key, callback) {
        if (hasTracked(key)) {
            return false;
        }

        callback();
        markTracked(key);
        return true;
    }

    function buildSendTo(label) {
        if (!label) {
            return null;
        }

        return `${CONVERSION_ID}/${label}`;
    }

    function sanitizeParams(params) {
        const nextParams = { ...params };

        if (typeof nextParams.value !== "number") {
            delete nextParams.value;
            delete nextParams.currency;
        }

        return nextParams;
    }

    function trackEvent(eventName, params = {}) {
        if (typeof window.gtag !== "function") {
            return false;
        }

        window.gtag("event", eventName, sanitizeParams(params));
        return true;
    }

    function trackConversion(name, params = {}) {
        const label = CONVERSION_LABELS[name];
        if (!label || typeof window.gtag !== "function") {
            return trackEvent(name, params);
        }

        window.gtag("event", "conversion", {
            send_to: buildSendTo(label),
            ...sanitizeParams(params),
        });
        return true;
    }

    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function gtag() {
        window.dataLayer.push(arguments);
    };

    ensureGoogleTagLoaded();
    window.gtag("js", new Date());
    window.gtag("config", CONVERSION_ID);

    window.SmartInvoiceAds = {
        conversionId: CONVERSION_ID,
        conversionLabels: CONVERSION_LABELS,
        buildSendTo,
        hasTracked,
        markTracked,
        trackOnce,
        trackEvent,
        trackConversion,
    };
})(window, document);
