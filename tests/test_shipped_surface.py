"""Nothing ships that nothing can reach.

652 lines of backend code and 12 npm dependencies were removed on 2026-09-05
because nothing imported, routed to, or referenced them. This is what stops
that coming back, and it exists in this shape because two naive versions of the
same check were written first and both were wrong:

  * A check that greps for a module's LEAF NAME reports
    `serp/widget_serializers.py` as used. Five files mention that name and
    every one of their imports resolves to `serp/custom_serializer/
    widget_serializers.py`, a different file. **A name is not a module**, so
    this resolves every import to the file it actually loads.

  * A check that only asks "who imports this?" reports management commands,
    WSGI/ASGI entry points and Django's `tests.py` stubs as dead, because all
    of them are reached BY NAME. Being reached by name is being reached, so
    those are listed explicitly, with a reason each.

Both lists below are decisions somebody wrote down, not inferences. Something
falling off the reachable set is a failure; something being on a list is a
choice, and `docs/SHIPPED-SURFACE.md` carries the longer reasoning.
"""

import ast
import json
import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
BACKEND = ROOT / "backend"
SKIP_DIRS = {"__pycache__", "static", "files", "logs", "templates", "migrations"}


# --- reached by name, not by import -----------------------------------------
# Removing any of these breaks the product even though nothing imports them.
REACHED_BY_NAME = {
    "serp.management.commands.rank_schedule":
        "manage.py rank_schedule, run every 15 minutes by the scheduler service",
    "serp.management.commands": "package marker for the command above",
    "serp.management": "package marker for the command above",
    "tracker.wsgi": "gunicorn, via tracker.wsgi:application in the prod overlay",
    "tracker.asgi": "Django's ASGI entry point",
    "tracker.settings": "DJANGO_SETTINGS_MODULE",
    "tracker.urls": "ROOT_URLCONF",
    "manage": "the command-line entry point itself",
    "account.ownership": "MIDDLEWARE, as the string account.ownership.UserIdOwnershipMiddleware",
    "scripts.seed_local": "python scripts/seed_local.py, in the dev stack's start command",
}

# --- parked FEATURES that live inside a live package ------------------------
# Same category as PARKED_PACKAGES, but a module rather than a whole app, so
# the package it sits in cannot excuse it.
PARKED_MODULES = {}

# --- parked: kept on purpose, deliberately unrouted -------------------------
# CLAUDE.md records the product decision; test_product_surface.py fails if any
# of these gets routed again. Do NOT propose removing them because nothing
# calls them -- that is the point of them.
# Empty on purpose since 2026-09-05: every parked package was removed rather
# than published. Add an entry here only for something deliberately kept on
# disk and deliberately unrouted, with the reason -- not for something that is
# merely unfinished.
PARKED_PACKAGES = {}

# Django reaches these by convention, per app.
BY_CONVENTION = {"__init__", "admin", "apps", "models", "urls", "views", "tests", "serializers"}


def _modules():
    """{dotted name: path} for every backend module."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(BACKEND):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if not name.endswith(".py"):
                continue
            path = Path(dirpath) / name
            dotted = str(path.relative_to(BACKEND)).replace(os.sep, "/")[:-3].replace("/", ".")
            if dotted.endswith(".__init__"):
                dotted = dotted[: -len(".__init__")]
            out[dotted] = path
    return out


_IMPORT_FROM = re.compile(r"^\s*from\s+([\w.]+)\s+import\s+(.+)$", re.M)
_IMPORT_PLAIN = re.compile(r"^\s*import\s+([\w.]+)", re.M)


def _importers(modules):
    """{dotted name: {paths that import it}} -- resolved to FILES, not names."""
    found = {name: set() for name in modules}
    for name, path in modules.items():
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        specs = set()
        for match in _IMPORT_FROM.finditer(source):
            package, names = match.group(1), match.group(2)
            specs.add(package)
            for imported in re.split(r"[,\s]+", names.replace("(", " ").replace(")", " ")):
                imported = imported.strip()
                if imported and imported not in ("import", "as", "*"):
                    specs.add(package + "." + imported)
        for match in _IMPORT_PLAIN.finditer(source):
            specs.add(match.group(1))
        for spec in specs:
            # A spec counts only if it resolves to a module that exists.
            if spec in modules and spec != name:
                found[spec].add(path)
    return found


def _is_excused(dotted, path=None):
    if dotted in REACHED_BY_NAME or dotted in PARKED_MODULES:
        return True
    if dotted.split(".")[0] in PARKED_PACKAGES:
        return True
    # A package marker: `_modules()` strips the trailing `.__init__`, so the
    # leaf-name check below cannot see it.
    if path is not None and path.name == "__init__.py":
        return True
    return dotted.split(".")[-1] in BY_CONVENTION


def test_every_backend_module_is_reachable():
    modules = _modules()
    importers = _importers(modules)
    orphans = sorted(
        (str(modules[name].relative_to(ROOT)).replace(os.sep, "/"), name)
        for name in modules
        if not importers[name] and not _is_excused(name, modules[name])
    )
    assert not orphans, (
        "%d backend module(s) are reachable by nothing -- no importer, no route, "
        "no command, no entry point, and not on the parked list:\n\n%s\n\n"
        "If one is genuinely reached by name, add it to REACHED_BY_NAME with the "
        "reason. If it is deliberately parked, add its package to "
        "PARKED_PACKAGES. If neither, it does not ship -- see "
        "docs/SHIPPED-SURFACE.md."
        % (len(orphans), "\n".join("    %s  (%s)" % o for o in orphans))
    )


def test_imports_resolve_to_files_not_names():
    """The trap that made `serp/widget_serializers.py` look alive.

    Its live sibling shares a leaf name. A leaf-name check credits this module
    with the sibling's importers; a file-resolving one does not.
    """
    modules = _modules()
    live = "serp.custom_serializer.widget_serializers"
    assert live in modules, "the live widget serializers moved; update this test"

    importers = _importers(modules)
    assert importers[live], "the live copy should have importers"

    # Had the deleted duplicate still existed, it would have had none of them.
    leaf = live.split(".")[-1]
    same_leaf = [name for name in modules if name.split(".")[-1] == leaf]
    assert same_leaf == [live], (
        "another module now shares the leaf name %r: %s. That is exactly the "
        "shape that hid dead code before -- confirm each one's importers "
        "resolve to it before trusting any of them." % (leaf, same_leaf)
    )


def test_parked_packages_are_not_reported_as_dead():
    modules = _modules()
    importers = _importers(modules)
    for package, reason in PARKED_PACKAGES.items():
        present = [name for name in modules if name.split(".")[0] == package]
        if not present:
            continue
        assert all(_is_excused(name, modules[name]) for name in present), (
            "%s is parked (%s) but some of its modules would be reported dead" % (package, reason)
        )


def test_reached_by_name_modules_still_exist():
    """A stale exception is worse than none: it excuses a module that is gone."""
    modules = _modules()
    listed = list(REACHED_BY_NAME) + list(PARKED_MODULES)
    missing = [name for name in listed if name not in modules and name != "manage"]
    assert not missing, (
        "REACHED_BY_NAME lists module(s) that no longer exist: %s. Remove the "
        "entry, or the list starts excusing things that are not there." % missing
    )


def test_the_deleted_modules_stay_deleted():
    for relative in (
        "backend/serp/widget_serializers.py",
        # The whole payment app went on 2026-09-05; see
        # test_billing_is_gone_entirely, which covers what used to be listed
        # here as a single file inside it.
        "backend/llmtracker/recompute.py",
        "backend/llmtracker/claude.py",
        "backend/serp/context_processors.py",
    ):
        assert not (ROOT / relative).exists(), (
            "%s is back. It was removed because nothing reached it; if it is "
            "needed now, something must import or route to it." % relative
        )


# --- dependencies -----------------------------------------------------------


def test_no_declared_dependency_is_unused_without_a_reason():
    """Unreferenced AND not a peer requirement of anything kept.

    The first pass of this analysis looked only at source references and would
    have removed `@emotion/react`, which MUI requires -- a failure that shows
    up at runtime, not at install.
    """
    package = json.loads((ROOT / "app" / "package.json").read_text(encoding="utf-8"))
    declared = set(package.get("dependencies") or {})

    source = []
    for dirpath, dirnames, filenames in os.walk(ROOT / "app" / "src"):
        for name in filenames:
            if name.endswith((".js", ".jsx", ".ts", ".tsx", ".scss", ".css")):
                source.append((Path(dirpath) / name).read_text(encoding="utf-8", errors="replace"))
    blob = "\n".join(source)

    unreferenced = sorted(d for d in declared if d not in blob)

    # Anything unreferenced must be a peer requirement of a referenced package.
    documented = (ROOT / "docs" / "SHIPPED-SURFACE.md").read_text(encoding="utf-8")
    undocumented = [d for d in unreferenced if d not in documented]
    assert not undocumented, (
        "%d dependency(ies) are declared, referenced nowhere in app/src, and not "
        "explained in docs/SHIPPED-SURFACE.md: %s\n\nEither remove them, or "
        "record why they are kept (a peer requirement is a real reason; being "
        "installed is not)." % (len(undocumented), undocumented)
    )


def test_the_removed_dependencies_stay_removed():
    package = json.loads((ROOT / "app" / "package.json").read_text(encoding="utf-8"))
    declared = set(package.get("dependencies") or {}) | set(package.get("devDependencies") or {})
    removed = {
        "@mui/styles", "@radix-ui/react-slot", "jwt-decode", "lodash", "lottie-react",
        "papaparse", "react-copy-to-clipboard", "react-google-login", "react-grid-layout",
        "react-table", "react-timer-hook", "use-state-with-callback",
    }
    back = sorted(removed & declared)
    assert not back, (
        "dependency(ies) removed on 2026-09-05 as unused are declared again: %s. "
        "If one is needed now, something in app/src should import it." % back
    )


# --- the frontend and the routing table -------------------------------------
#
# The backend check above only ever looked at Python modules. On 2026-09-05 a
# sweep found four React modules nothing imported and three routed-decorator
# views nothing routed -- 160 lines of billing left inside a live module, and a
# second `project_export.js` under `competitor/` that was invisible because
# `serp_rank_table.js` imports `"./components/project_export"` and that
# resolves to the copy under `serpRank/`. Same leaf-name trap as above, in
# JavaScript this time. Resolve specifiers to FILES.

_SPEC = re.compile(r"""(?:from\s+|import\s*\(\s*|require\s*\(\s*)['"]([^'"]+)['"]""")

# Reached by the bundler or the toolchain, not by an import.
FRONTEND_ENTRY = {"index.js", "App.js", "setupTests.js", "reportWebVitals.js", "vite-env.d.ts"}


def _frontend_modules():
    src = ROOT / "app" / "src"
    out = []
    for suffix in ("*.js", "*.jsx", "*.ts", "*.tsx"):
        out.extend(p for p in src.rglob(suffix) if "node_modules" not in str(p))
    return out


def test_every_frontend_module_is_imported():
    src = ROOT / "app" / "src"
    modules = _frontend_modules()
    imported = set()
    for path in modules:
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in _SPEC.finditer(text):
            spec = match.group(1)
            if spec.startswith("."):
                base = (path.parent / spec).resolve()
            elif spec.startswith("@/"):
                base = (src / spec[2:]).resolve()
            else:
                continue  # a package, not a file in this tree
            for candidate in (
                base,
                base.with_suffix(".js"), base.with_suffix(".jsx"),
                base.with_suffix(".ts"), base.with_suffix(".tsx"),
                base / "index.js", base / "index.jsx",
                base / "index.ts", base / "index.tsx",
            ):
                if candidate.is_file():
                    imported.add(candidate.resolve())
                    break

    orphans = sorted(
        str(p.relative_to(ROOT)).replace(os.sep, "/")
        for p in modules
        if p.resolve() not in imported and p.name not in FRONTEND_ENTRY
    )
    assert not orphans, (
        "%d frontend module(s) are imported by nothing -- not by a route, not "
        "by a React.lazy call, not by a sibling:\n\n%s\n\nIf one is an entry "
        "point, add it to FRONTEND_ENTRY with a reason. Otherwise it does not "
        "ship." % (len(orphans), "\n".join("    " + o for o in orphans))
    )


# A view carrying one of these decorators is meant to answer a request.
VIEW_DECORATORS = ("api_view", "csrf_exempt", "permission_classes", "cron_only")


def test_every_view_is_routed():
    routed = set()
    for urls in (ROOT / "backend").rglob("urls.py"):
        for line in urls.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip().startswith("#"):
                continue  # a commented-out route routes nothing
            match = re.search(r"(?:path|re_path|url)\s*\(\s*[^,]+,\s*([A-Za-z_][\w.]*)", line)
            if match:
                routed.add(match.group(1).split(".")[-1])

    unrouted = []
    for py in (ROOT / "backend").rglob("*.py"):
        rel = str(py).replace(os.sep, "/")
        if "__pycache__" in rel or "/migrations/" in rel:
            continue
        package = str(py.relative_to(ROOT / "backend")).replace(os.sep, "/").split("/")[0]
        if package in PARKED_PACKAGES:
            continue
        text = py.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        module = str(py.relative_to(ROOT / "backend")).replace(os.sep, "/")[:-3].replace("/", ".")
        if module in PARKED_MODULES:
            continue
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef) or node.name in routed:
                continue
            decorators = []
            for d in node.decorator_list:
                target = d.func if isinstance(d, ast.Call) else d
                decorators.append(getattr(target, "id", getattr(target, "attr", "")))
            if not any(name in VIEW_DECORATORS for name in decorators):
                continue
            # Reached by name from elsewhere in the backend still counts --
            # but a SAME-NAMED DEFINITION in another file is not a reference.
            # Two dead views both called `aktest`, in views.py and widget.py,
            # each satisfied a naive check by being the other's "reference".
            # A commented-out line is not a reference either.
            pattern = re.compile(r"%s" % re.escape(node.name))
            referenced = False
            for other in (ROOT / "backend").rglob("*.py"):
                if other == py or "__pycache__" in str(other):
                    continue
                for line in other.read_text(encoding="utf-8", errors="replace").splitlines():
                    stripped = line.strip()
                    if stripped.startswith("#") or stripped.startswith("def %s" % node.name):
                        continue
                    if pattern.search(line):
                        referenced = True
                        break
                if referenced:
                    break
            if not referenced:
                unrouted.append("%s:%d  %s" % (rel[len(str(ROOT).replace(os.sep, "/")) + 1:], node.lineno, node.name))

    assert not unrouted, (
        "%d view(s) carry a request decorator but are routed by nothing and "
        "referenced by nothing:\n\n%s\n\nAn endpoint no URL reaches is dead "
        "surface. Route it or remove it." % (len(unrouted), "\n".join("    " + u for u in unrouted))
    )


def test_the_removed_frontend_modules_stay_removed():
    for relative in (
        "app/src/pages/account/icons/icons.js",
        "app/src/pages/commonComponents/project_toggle.js",
        "app/src/pages/commonComponents/tool_tip.js",
        "app/src/pages/competitor/components/project_export.js",
    ):
        assert not (ROOT / relative).exists(), (
            "%s is back; nothing imported it when it was removed" % relative
        )


def test_billing_views_stay_out_of_the_live_serp_app():
    """160 lines of billing sat in `serp/views.py`, a live module, so the
    parked-package rule never covered them. The product is BYOK and
    self-hosted: there is nothing to sell."""
    views = (ROOT / "backend" / "serp" / "views.py").read_text(encoding="utf-8")
    for name in ("def billing_plans", "def billing_plans_pdf", "def freemumcrdtupdate"):
        assert name not in views, "%s is back in serp/views.py" % name


# --- documentation ----------------------------------------------------------
#
# The other direction of the same rule. Source comments cite `docs/*.md` as the
# contract they implement -- `docs/DESIGN.md` alone is named in 44 files. On
# 2026-09-05, 35 internal working notes were deleted from `docs/`; had the
# design docs gone with them, a published repo would have shipped 56 files
# pointing at documentation that is not there. A citation is a dependency.

_DOC_REF = re.compile(r"docs/[A-Za-z0-9_.-]+\.md")
_MD_LINK = re.compile(r"\]\((docs/[^)#]+\.md|[A-Z][A-Z_-]*\.md)\)")


def test_every_doc_cited_from_source_exists():
    cited = {}
    for root in ("app/src", "backend", "engine", "shared", "tests"):
        for dirpath, dirnames, filenames in os.walk(ROOT / root):
            dirnames[:] = [d for d in dirnames if d not in ("__pycache__", "node_modules")]
            for name in filenames:
                if not name.endswith((".py", ".js", ".jsx", ".scss")):
                    continue
                path = Path(dirpath) / name
                text = path.read_text(encoding="utf-8", errors="replace")
                for target in set(_DOC_REF.findall(text)):
                    cited.setdefault(target, set()).add(
                        str(path.relative_to(ROOT)).replace(os.sep, "/")
                    )

    missing = {t: sorted(f) for t, f in cited.items() if not (ROOT / t).exists()}
    assert not missing, (
        "source cites %d document(s) that do not exist:\n\n%s\n\nEither restore "
        "the document or remove the citation -- a comment pointing at a missing "
        "file is worse than no comment."
        % (len(missing), "\n".join(
            "    %s\n        cited by: %s" % (t, ", ".join(f[:5]))
            for t, f in sorted(missing.items())
        ))
    )


def test_the_readme_and_contributing_links_resolve():
    broken = []
    for source in ("README.md", "CONTRIBUTING.md"):
        text = (ROOT / source).read_text(encoding="utf-8")
        for target in _MD_LINK.findall(text):
            if not (ROOT / target).exists():
                broken.append("%s -> %s" % (source, target))
    assert not broken, "broken documentation link(s): %s" % broken


def test_billing_is_gone_entirely():
    """The product is bring-your-own-key and self-hosted. There is no plan to
    sell, no checkout, and no storefront -- so 3,245 lines of subscription,
    Stripe and redemption code were removed on 2026-09-05, along with
    `serp/searchvolume.py`, whose only reason to import `payment` was a
    metered search-volume feature this build does not ship.

    Its one live tie was a Django admin registration in `serp/admin.py`; the
    other three importers had the models in an import line and never used them.
    """
    assert not (ROOT / "backend" / "payment").exists(), "the payment app is back"
    assert not (ROOT / "backend" / "serp" / "searchvolume.py").exists()

    settings = (ROOT / "backend" / "tracker" / "settings.py").read_text(encoding="utf-8")
    assert '"payment"' not in settings and '"payment.redeem"' not in settings, (
        "payment is in INSTALLED_APPS again; Django will fail to start without "
        "the package, and ship its tables if it is restored"
    )

    for relative in (
        "backend/serp/admin.py",
        "backend/serp/serializers.py",
        "backend/serp/custom_serializer/report_serializers.py",
        "backend/serp/custom_serializer/widget_serializers.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "from payment" not in source, "%s imports payment again" % relative


def test_the_parked_packages_are_gone():
    """`kw_research`, `pageaudit` and `content_gap` were 5,580 lines that no
    URL reached, and `kw_research` still named a storefront. Keeping them on
    disk meant publishing them.

    Each had exactly one thread into live code, and none of the three was
    load-bearing: `serp/views.py` imported `kw_research.models` with a wildcard
    and used one class, in a `gresultpage` branch the single caller has never
    been able to reach; `serp/serializers.py` counted `CGASearch` rows into a
    `cGLT` field no screen reads.
    """
    for package in ("kw_research", "pageaudit", "content_gap", "payment"):
        assert not (ROOT / "backend" / package).exists(), "%s is back" % package

    settings = (ROOT / "backend" / "tracker" / "settings.py").read_text(encoding="utf-8")
    for package in ("kw_research", "pageaudit", "content_gap", "payment"):
        assert '"%s"' % package not in settings, (
            "%s is in INSTALLED_APPS but not on disk -- Django will not start" % package
        )

    views = (ROOT / "backend" / "serp" / "views.py").read_text(encoding="utf-8")
    assert "kw_research" not in views and "KeywordResearch" not in views
    serializers = (ROOT / "backend" / "serp" / "serializers.py").read_text(encoding="utf-8")
    assert "content_gap" not in serializers and "cGLT" not in serializers
