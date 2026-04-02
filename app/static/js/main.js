document.addEventListener("DOMContentLoaded", () => {
    const permissions = new Set(window.APP_PERMISSIONS || []);
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const themedPage = document.body.dataset.dashboardTheme === "1";

    const hasPermission = (code) => permissions.has(code);

    const showPermissionDenied = (action) => {
        const message = `You have no permission to ${action}.`;
        if (typeof window.showNotification === "function") {
            window.showNotification(message, "danger");
            return;
        }
        alert(message);
    };

    if (themedPage && !prefersReducedMotion) {
        let leaving = false;

        const startRouteTransition = (navigate) => {
            if (leaving) return;
            leaving = true;
            document.body.classList.add("theme-route-leaving");
            window.setTimeout(() => {
                navigate();
            }, 220);
        };

        document.addEventListener("click", (event) => {
            const link = event.target.closest("a[href]");
            if (!link || leaving || event.defaultPrevented) return;
            if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
            if (link.target && link.target !== "_self") return;
            if (link.hasAttribute("download") || link.dataset.noTransition === "true") return;

            const rawHref = link.getAttribute("href");
            if (!rawHref || rawHref.startsWith("#") || rawHref.startsWith("javascript:")) return;
            if (rawHref.startsWith("mailto:") || rawHref.startsWith("tel:")) return;

            const nextUrl = new URL(link.href, window.location.href);
            if (nextUrl.origin !== window.location.origin) return;
            if (nextUrl.href === window.location.href) return;

            event.preventDefault();
            startRouteTransition(() => {
                window.location.href = nextUrl.href;
            });
        });

        document.querySelectorAll("form[action]").forEach((form) => {
            form.addEventListener("submit", (event) => {
                if (leaving) {
                    event.preventDefault();
                    return;
                }

                if (typeof form.checkValidity === "function" && !form.checkValidity()) {
                    return;
                }

                event.preventDefault();
                startRouteTransition(() => {
                    HTMLFormElement.prototype.submit.call(form);
                });
            });
        });

        window.addEventListener("pageshow", () => {
            leaving = false;
            document.body.classList.remove("theme-route-leaving");
        });
    }

    document.addEventListener("click", (event) => {
        const target = event.target.closest("[data-permission]");
        if (!target) return;
        const permission = target.dataset.permission;
        if (!permission || hasPermission(permission)) return;
        event.preventDefault();
        event.stopPropagation();
        const action = target.dataset.action || "perform this action";
        showPermissionDenied(action);
    });

    const pwd = document.querySelector('input[name="password"]');
    if (!pwd) return;

    pwd.addEventListener("input", () => {
        const msg = document.querySelector("#passwordHelp");
        if (!msg) return;

        const v = pwd.value;
        const strong = v.length >= 6;

        msg.textContent = strong
            ? "Password length looks good."
            : "Use at least 6 characters.";
        msg.className = strong ? "form-text text-success" : "form-text text-danger";
    });
});
