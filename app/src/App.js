import React, { useState, useEffect, useRef, Suspense } from "react";
import "./assets/styles/style.scss";
import { BrowserRouter as Router, Switch } from "react-router-dom";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { ToastContainer, Slide } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import LoadingBar from "react-top-loading-bar";

// Importing Pages
import Login from "./pages/welcome/login";
const LandingPage = React.lazy(() => import("./pages/landing/LandingPage"));
import Signup from "./pages/welcome/signup";
import Register from "./pages/welcome/register";
import ResetPassword from "./pages/welcome/resetPassword";
import ForgotPassword from "./pages/welcome/forgotPassword";
import PrivacyPolicy from "./pages/welcome/privacy_policy";
import Notfound from "./pages/404";

import PrivateRoute from './pages/routeComponents/private_route';
import PublicRoute from './pages/routeComponents/public_route';
import TermsAndConditions from "./pages/welcome/terms_and_conditions";



// Design tokens — mirrored from src/assets/styles/modules/_tokens.scss. That
// file and this object are the only two places a raw value is written.
// Contract: docs/DESIGN.md.
const t = {
  ink: "#0f0f10",
  ink2: "#3d3f45",
  ink3: "#6b6e76",
  ink4: "#9aa0a8",

  paper: "#ffffff",
  surface: "#ffffff",
  surface2: "#f5f5f6",

  line: "rgba(15, 15, 16, 0.12)",
  line2: "rgba(15, 15, 16, 0.06)",

  accent: "#1a3cff",
  accentWeak: "#e8ecff",
  // The "where am I" colour, and nothing else -- active rail item, active tab,
  // "new" dot. Separate from accent so an active nav item stops reading as a
  // call to action. See the note in _tokens.scss for the derivation.
  navAccent: "#791fba",
  navAccentWeak: "#f1e9fc",
  up: "#12b76a",
  down: "#d92d20",
  flat: "#98a2b3",
  warn: "#dc6803",

  // Derived from the tokens above, never a colour in their own right: the
  // primary button's hover fill and the wash under a destructive control.
  inkHover: "#26262a",
  downWash: "rgba(217, 45, 32, 0.06)",

  rSm: 8,
  rMd: 14,
  rLg: 20,
  rPill: 999,

  ctrl: 38, // every control is 38px tall — DESIGN.md "minimum hit area 38x38"
};

// "Regular" / "SemiBold" / "Bold" are the legacy family aliases declared in
// _tokens.scss; all three now resolve to Space Grotesk. Hundreds of call sites
// name them, so they stay — with the real stack behind them as a fallback.
// There is no "Medium" face, so weight 500 is never requested.
const fontStack =
  '"Space Grotesk", "Be Vietnam Pro", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
const regular = '"Regular", ' + fontStack;
const semibold = '"SemiBold", ' + fontStack;

const dur = "160ms";
const ease = "cubic-bezier(0.2, 0, 0, 1)";
// Only these properties may animate — DESIGN.md "Space, radius, motion".
const transition = ["color", "background-color", "border-color", "opacity", "transform"]
  .map(function (prop) {
    return prop + " " + dur + " " + ease;
  })
  .join(", ");

// Focus is always visible, in two flavours: an outline for anything that sits
// on the page, a ring for fields. Never `outline: none` without a replacement.
const focusRing = {
  outline: "2px solid " + t.accent,
  outlineOffset: "2px",
};
const inputFocus = {
  borderColor: t.accent,
  boxShadow: "0 0 0 3px " + t.accentWeak,
};

// Nothing is elevated except the things that genuinely float. MUI needs exactly
// 25 entries, so only the indices its floating components ask for carry a
// shadow: Snackbar 6, Menu/Popover/Autocomplete 8, Drawer 16, Dialog 24.
const float = {
  6: "0 2px 6px rgba(15,15,16,0.06), 0 12px 28px rgba(15,15,16,0.08)",
  8: "0 2px 6px rgba(15,15,16,0.06), 0 12px 28px rgba(15,15,16,0.08)",
  16: "0 4px 10px rgba(15,15,16,0.06), 0 20px 44px rgba(15,15,16,0.10)",
  24: "0 4px 10px rgba(15,15,16,0.06), 0 24px 56px rgba(15,15,16,0.12)",
};
const shadows = Array.from({ length: 25 }, function (_, i) {
  return float[i] || "none";
});

const theme = createTheme({
  breakpoints: {
    values: {
      xs: 0,
      sm: 575,
      md: 767,
      lg: 991,
      xl: 1199,
    },
  },
  shape: {
    borderRadius: t.rMd,
  },
  shadows: shadows,
  palette: {
    primary: {
      main: t.accent,
      dark: t.accent,
      light: t.accentWeak,
      contrastText: t.surface,
    },
    secondary: {
      main: t.ink2,
      light: t.surface2,
      dark: t.ink,
      contrastText: t.surface,
    },
    // `color="white"` is how the secondary button is spelled at ~130 call sites.
    white: {
      main: t.surface,
      contrastText: t.ink,
    },
    success: { main: t.up, contrastText: t.surface },
    error: { main: t.down, contrastText: t.surface },
    warning: { main: t.warn, contrastText: t.surface },
    info: { main: t.accent, contrastText: t.surface },
    grey: {
      100: t.surface2,
      500: t.flat,
    },
    text: {
      primary: t.ink,
      secondary: t.ink3,
      disabled: t.ink4,
    },
    background: {
      default: t.paper,
      paper: t.surface,
    },
    divider: t.line,
    action: {
      hover: t.surface2,
      selected: t.accentWeak,
      focus: t.accentWeak,
      disabled: t.ink4,
      disabledBackground: t.surface2,
    },
  },
  typography: {
    fontFamily: fontStack,
    fontSize: 14,
    color: t.ink,
    // page title
    h1: {
      fontFamily: semibold,
      fontWeight: 600,
      fontSize: 26,
      lineHeight: 1.2,
      letterSpacing: "-0.03em",
      marginBottom: "0 !important",
    },
    h2: {
      fontFamily: semibold,
      fontWeight: 600,
      fontSize: 20,
      lineHeight: 1.25,
      letterSpacing: "-0.025em",
      marginBottom: "0 !important",
    },
    h3: {
      fontFamily: semibold,
      fontWeight: 600,
      fontSize: 17,
      lineHeight: 1.3,
      letterSpacing: "-0.02em",
      marginBottom: "0 !important",
    },
    // h4 reads as muted running text across the app, not as a heading.
    h4: {
      fontFamily: regular,
      fontWeight: 400,
      fontSize: 14,
      lineHeight: 1.55,
      letterSpacing: 0,
      color: t.ink3,
      marginBottom: "0 !important",
    },
    // card title
    h5: {
      fontFamily: semibold,
      fontWeight: 600,
      fontSize: 15,
      lineHeight: 1.35,
      letterSpacing: "-0.015em",
      marginBottom: "0 !important",
    },
    h6: {
      fontFamily: semibold,
      fontWeight: 600,
      fontSize: 14,
      lineHeight: 1.4,
      letterSpacing: "-0.01em",
      marginBottom: "0 !important",
    },
    subtitle1: {
      fontFamily: semibold,
      fontWeight: 600,
      fontSize: 14,
      lineHeight: 1.45,
      letterSpacing: "-0.01em",
    },
    subtitle2: {
      fontFamily: semibold,
      fontWeight: 600,
      fontSize: 12.5,
      lineHeight: 1.45,
      letterSpacing: 0,
      color: t.ink3,
    },
    body1: {
      fontFamily: regular,
      fontWeight: 400,
      fontSize: 14,
      lineHeight: 1.55,
      letterSpacing: 0,
    },
    body2: {
      fontFamily: regular,
      fontWeight: 400,
      fontSize: 12.5,
      lineHeight: 1.5,
      letterSpacing: 0,
      color: t.ink3,
    },
    caption: {
      fontFamily: regular,
      fontWeight: 400,
      fontSize: 12.5,
      lineHeight: 1.45,
      color: t.ink3,
    },
    // micro-label
    overline: {
      fontFamily: semibold,
      fontWeight: 600,
      fontSize: 11,
      lineHeight: 1.4,
      letterSpacing: "0.08em",
      textTransform: "uppercase",
      color: t.ink3,
    },
    button: {
      fontFamily: semibold,
      fontWeight: 600,
      fontSize: 13.5,
      textTransform: "none",
      letterSpacing: 0,
    },
    // legacy custom variants — kept because call sites name them
    p: {
      fontFamily: regular,
      fontSize: 14,
      lineHeight: 1.55,
      marginBottom: "0 !important",
    },
    p1: {
      fontFamily: regular,
      fontSize: 12.5,
      lineHeight: 1.45,
      color: t.ink3,
      marginBottom: "0 !important",
    },
    p2: {
      fontFamily: regular,
      fontSize: 16,
      lineHeight: 1.5,
      marginBottom: "0 !important",
    },
  },
  components: {
    // ---- buttons --------------------------------------------------------
    // primary     variant="contained"
    // secondary   variant="outlined", or color="white" on a contained button
    // ghost       variant="text"
    // destructive color="error", whatever the variant
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          fontFamily: semibold,
          fontWeight: 600,
          fontSize: 13.5,
          letterSpacing: 0,
          textTransform: "none",
          minWidth: t.ctrl,
          height: t.ctrl,
          padding: "0 18px",
          borderRadius: t.rPill,
          boxShadow: "none",
          transition: transition,
          "&:hover": { boxShadow: "none" },
          "&.Mui-focusVisible": focusRing,
          "&.Mui-disabled": { color: t.ink4 },
        },
        sizeSmall: {
          height: 32,
          padding: "0 14px",
          fontSize: 12.5,
          borderRadius: t.rPill,
        },
        sizeLarge: {
          height: 44,
          padding: "0 22px",
          fontSize: 14.5,
          borderRadius: t.rPill,
        },
        contained: {
          backgroundColor: t.ink,
          color: t.surface,
          border: "1px solid " + t.ink,
          "&:hover": {
            backgroundColor: t.inkHover,
            borderColor: t.inkHover,
          },
          "&.Mui-disabled": {
            backgroundColor: t.surface2,
            borderColor: "transparent",
            color: t.ink4,
          },
        },
        containedWhite: {
          backgroundColor: t.surface,
          color: t.ink,
          border: "1px solid " + t.line,
          "&:hover": {
            backgroundColor: t.surface2,
            borderColor: t.line,
          },
        },
        containedSecondary: {
          backgroundColor: t.surface,
          color: t.ink,
          border: "1px solid " + t.line,
          "&:hover": {
            backgroundColor: t.surface2,
            borderColor: t.line,
          },
        },
        containedError: {
          backgroundColor: "transparent",
          color: t.down,
          border: "1px solid " + t.down,
          "&:hover": {
            backgroundColor: t.downWash,
            borderColor: t.down,
          },
        },
        outlined: {
          backgroundColor: t.surface,
          color: t.ink,
          borderColor: t.line,
          "&:hover": {
            backgroundColor: t.surface2,
            borderColor: t.line,
          },
          "&.Mui-disabled": {
            borderColor: t.line,
            color: t.ink4,
          },
        },
        outlinedPrimary: {
          color: t.ink,
          borderColor: t.line,
          "&:hover": {
            backgroundColor: t.surface2,
            borderColor: t.line,
          },
        },
        outlinedError: {
          backgroundColor: "transparent",
          color: t.down,
          borderColor: t.down,
          "&:hover": {
            backgroundColor: t.downWash,
            borderColor: t.down,
          },
        },
        text: {
          backgroundColor: "transparent",
          color: t.ink2,
          "&:hover": { backgroundColor: t.surface2 },
        },
        textPrimary: {
          color: t.ink2,
          "&:hover": { backgroundColor: t.surface2 },
        },
        textError: {
          color: t.down,
          "&:hover": { backgroundColor: t.downWash },
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          width: t.ctrl,
          height: t.ctrl,
          borderRadius: t.rPill,
          border: "1px solid " + t.line,
          backgroundColor: t.surface,
          color: t.ink2,
          transition: transition,
          "&:hover": {
            backgroundColor: t.surface2,
            borderColor: t.line,
            color: t.ink,
          },
          "&.Mui-focusVisible": focusRing,
          "&.Mui-disabled": { color: t.ink4 },
        },
        sizeSmall: {
          width: 32,
          height: 32,
        },
        colorError: {
          color: t.down,
          "&:hover": { backgroundColor: t.downWash, color: t.down },
        },
      },
    },
    MuiToggleButton: {
      styleOverrides: {
        root: {
          fontFamily: semibold,
          fontWeight: 600,
          fontSize: 13.5,
          letterSpacing: 0,
          textTransform: "none",
          height: t.ctrl,
          padding: "0 16px",
          color: t.ink3,
          borderColor: t.line,
          borderRadius: t.rPill,
          transition: transition,
          "&:hover": { backgroundColor: t.surface2 },
          "&.Mui-selected": {
            color: t.accent,
            backgroundColor: t.accentWeak,
            "&:hover": { backgroundColor: t.accentWeak },
          },
          "&.Mui-focusVisible": focusRing,
        },
      },
    },

    // ---- fields ---------------------------------------------------------
    MuiInputLabel: {
      styleOverrides: {
        root: {
          fontFamily: semibold,
          fontWeight: 600,
          fontSize: 13,
          letterSpacing: 0,
          color: t.ink2,
          "&.Mui-focused": { color: t.ink2 },
          "&.Mui-error": { color: t.down },
        },
      },
    },
    MuiInputBase: {
      styleOverrides: {
        root: {
          fontFamily: regular,
          fontSize: 14,
          color: t.ink,
        },
        input: {
          "&::placeholder": {
            color: t.ink4,
            opacity: 1,
          },
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          backgroundColor: t.surface,
          borderRadius: t.rSm,
          transition: transition,
          "&:hover .MuiOutlinedInput-notchedOutline": {
            borderColor: t.ink4,
          },
          "&.Mui-focused": inputFocus,
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderWidth: 1,
            borderColor: t.accent,
          },
          "&.Mui-error .MuiOutlinedInput-notchedOutline": {
            borderColor: t.down,
          },
          "&.Mui-disabled": {
            backgroundColor: t.surface2,
            "& .MuiOutlinedInput-notchedOutline": { borderColor: t.line },
          },
          "&.MuiInputBase-multiline": {
            padding: "10px 12px",
          },
        },
        input: {
          height: t.ctrl,
          boxSizing: "border-box",
          padding: "0 12px",
          fontSize: 14,
        },
        inputSizeSmall: {
          height: 32,
        },
        inputMultiline: {
          height: "auto",
          padding: 0,
        },
        notchedOutline: {
          borderColor: t.line,
          borderWidth: 1,
          top: 0,
          "& legend": { float: "left" },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          "& .MuiOutlinedInput-root": {
            backgroundColor: t.surface,
            borderRadius: t.rSm,
          },
          "& fieldset": {
            top: 0,
            "& legend": { float: "left" },
          },
        },
      },
    },
    MuiFormHelperText: {
      styleOverrides: {
        root: {
          fontFamily: regular,
          fontSize: 12.5,
          lineHeight: 1.45,
          marginLeft: 2,
          color: t.ink3,
          "&.Mui-error": { color: t.down },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        select: {
          width: "100%",
          minHeight: t.ctrl,
          display: "flex",
          alignItems: "center",
          padding: "0 12px",
          fontSize: 14,
          "&::placeholder": {
            color: t.ink4,
            opacity: 1,
          },
        },
        icon: {
          color: t.ink3,
        },
      },
    },
    MuiCheckbox: {
      styleOverrides: {
        root: {
          color: t.ink3,
          transition: transition,
          "&.Mui-checked": { color: t.accent },
          "&.Mui-focusVisible": focusRing,
          "&.Mui-disabled": { color: t.ink4 },
        },
      },
    },
    MuiRadio: {
      styleOverrides: {
        root: {
          color: t.ink3,
          transition: transition,
          "&.Mui-checked": { color: t.accent },
          "&.Mui-focusVisible": focusRing,
          "&.Mui-disabled": { color: t.ink4 },
        },
      },
    },
    MuiSwitch: {
      styleOverrides: {
        // The legacy sheet pins the switch geometry with !important, so only
        // the colours are the theme's to give.
        track: {
          backgroundColor: t.ink4,
          opacity: 1,
        },
        thumb: {
          backgroundColor: t.surface,
          boxShadow: "none",
        },
        switchBase: {
          color: t.surface,
          "&.Mui-checked": { color: t.surface },
          "&.Mui-checked + .MuiSwitch-track": {
            backgroundColor: t.accent,
            opacity: 1,
          },
          "&.Mui-focusVisible .MuiSwitch-thumb": focusRing,
          "&.Mui-disabled + .MuiSwitch-track": {
            backgroundColor: t.surface2,
            opacity: 1,
          },
        },
      },
    },
    MuiFormControlLabel: {
      styleOverrides: {
        label: {
          fontFamily: regular,
          fontSize: 14,
          color: t.ink,
        },
      },
    },

    // ---- surfaces -------------------------------------------------------
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
          backgroundColor: t.surface,
          borderRadius: t.rMd,
          color: t.ink,
        },
        outlined: {
          border: "1px solid " + t.line,
        },
      },
    },
    MuiCard: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          backgroundColor: t.surface,
          borderRadius: t.rMd,
          border: "1px solid " + t.line,
          boxShadow: "none",
        },
      },
    },
    MuiCardHeader: {
      styleOverrides: {
        root: {
          padding: "20px 24px 16px 24px",
        },
        title: {
          fontFamily: semibold,
          fontWeight: 600,
          fontSize: 15,
          letterSpacing: "-0.015em",
        },
        subheader: {
          fontFamily: regular,
          fontSize: 12.5,
          color: t.ink3,
        },
      },
    },
    MuiCardContent: {
      styleOverrides: {
        root: {
          padding: 24,
          "&:last-child": {
            paddingBottom: 24,
          },
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: t.line,
        },
      },
    },
    MuiList: {
      styleOverrides: {
        root: {
          li: {
            fontSize: 13.5,
          },
        },
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: {
          backgroundColor: t.surface,
          borderRadius: t.rMd,
          border: "1px solid " + t.line,
          boxShadow: float[8],
          marginTop: 6,
        },
        list: {
          padding: 6,
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          fontFamily: regular,
          fontSize: 13.5,
          minHeight: 36,
          padding: "8px 12px",
          borderRadius: t.rSm,
          color: t.ink,
          transition: transition,
          "&:hover": { backgroundColor: t.surface2 },
          "&.Mui-focusVisible": focusRing,
          "&.Mui-selected": {
            backgroundColor: t.accentWeak,
            color: t.accent,
            "&:hover": { backgroundColor: t.accentWeak },
          },
        },
      },
    },
    MuiPopover: {
      styleOverrides: {
        paper: {
          backgroundColor: t.surface,
          borderRadius: t.rMd,
          border: "1px solid " + t.line,
          boxShadow: float[8],
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: t.surface,
          borderRadius: 0,
          borderColor: t.line,
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: t.surface,
          color: t.ink,
          maxWidth: 330,
          fontFamily: regular,
          fontSize: 12.5,
          lineHeight: 1.5,
          padding: "10px 12px",
          border: "1px solid " + t.line,
          borderRadius: t.rSm,
          boxShadow: float[8],
        },
        arrow: {
          color: t.surface,
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          backgroundColor: t.surface,
          borderRadius: t.rLg,
          border: "1px solid " + t.line,
          boxShadow: float[24],
        },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: {
          fontFamily: semibold,
          fontWeight: 600,
          fontSize: 17,
          letterSpacing: "-0.02em",
          padding: "24px 24px 8px 24px",
        },
      },
    },
    MuiDialogContent: {
      styleOverrides: {
        root: {
          padding: "8px 24px",
        },
      },
    },
    MuiDialogActions: {
      styleOverrides: {
        root: {
          padding: "16px 24px 24px 24px",
          gap: 8,
        },
      },
    },
    MuiBackdrop: {
      styleOverrides: {
        root: {
          backgroundColor: "rgba(15, 15, 16, 0.32)",
        },
      },
    },

    // ---- feedback -------------------------------------------------------
    // No pastel fills: an alert is a card and its icon carries the meaning.
    MuiAlert: {
      styleOverrides: {
        root: {
          backgroundColor: t.surface,
          color: t.ink,
          border: "1px solid " + t.line,
          borderRadius: t.rMd,
          fontFamily: regular,
          fontSize: 13.5,
        },
        standardSuccess: { "& .MuiAlert-icon": { color: t.up } },
        standardError: { "& .MuiAlert-icon": { color: t.down } },
        standardWarning: { "& .MuiAlert-icon": { color: t.warn } },
        standardInfo: { "& .MuiAlert-icon": { color: t.accent } },
        outlinedSuccess: { "& .MuiAlert-icon": { color: t.up } },
        outlinedError: { "& .MuiAlert-icon": { color: t.down } },
        outlinedWarning: { "& .MuiAlert-icon": { color: t.warn } },
        outlinedInfo: { "& .MuiAlert-icon": { color: t.accent } },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          height: 6,
          borderRadius: t.rPill,
          backgroundColor: t.surface2,
        },
        bar: {
          borderRadius: t.rPill,
          backgroundColor: t.ink,
        },
      },
    },
    MuiSkeleton: {
      styleOverrides: {
        root: {
          backgroundColor: t.surface2,
          borderRadius: t.rSm,
        },
        circular: {
          borderRadius: t.rPill,
        },
      },
    },
    MuiBadge: {
      styleOverrides: {
        badge: {
          fontFamily: semibold,
          fontWeight: 600,
          fontSize: 11,
          letterSpacing: 0,
          height: 18,
          minWidth: 18,
          padding: "0 5px",
          borderRadius: t.rPill,
        },
        colorPrimary: {
          backgroundColor: t.accent,
          color: t.surface,
        },
        colorError: {
          backgroundColor: t.down,
          color: t.surface,
        },
      },
    },

    // ---- navigation -----------------------------------------------------
    MuiTabs: {
      styleOverrides: {
        root: {
          minHeight: t.ctrl,
        },
        flexContainer: {
          gap: 4,
        },
        // the selected pill is the indicator
        indicator: {
          height: 0,
          backgroundColor: "transparent",
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          fontFamily: semibold,
          fontWeight: 600,
          fontSize: 13.5,
          letterSpacing: 0,
          textTransform: "none",
          minHeight: 34,
          padding: "0 16px",
          borderRadius: t.rPill,
          color: t.ink3,
          transition: transition,
          "&:hover": {
            backgroundColor: t.surface2,
            color: t.ink,
          },
          // One selected state for every tab strip in the app, and the same
          // one the rail uses: --nav-accent-weak fill, --nav-accent label.
          // "Which section am I in" and "which page am I on" then answer in
          // one colour, and it is not the colour that means "act on this".
          "&.Mui-selected": {
            color: t.navAccent,
            backgroundColor: t.navAccentWeak,
            "&:hover": {
              color: t.navAccent,
              backgroundColor: t.navAccentWeak,
            },
          },
          "&.Mui-focusVisible": focusRing,
        },
      },
    },
    MuiLink: {
      defaultProps: {
        underline: "hover",
      },
      styleOverrides: {
        root: {
          color: t.accent,
          textDecorationColor: t.line,
          "&.Mui-focusVisible": focusRing,
        },
      },
    },
    MuiPagination: {
      styleOverrides: {
        ul: {
          gap: 2,
        },
      },
    },
    MuiPaginationItem: {
      styleOverrides: {
        root: {
          fontFamily: semibold,
          fontWeight: 600,
          fontSize: 13,
          minWidth: 32,
          height: 32,
          borderRadius: t.rPill,
          color: t.ink2,
          transition: transition,
          "&:hover": { backgroundColor: t.surface2 },
          "&.Mui-focusVisible": focusRing,
          "&.Mui-selected": {
            backgroundColor: t.accentWeak,
            color: t.accent,
            "&:hover": { backgroundColor: t.accentWeak },
          },
        },
      },
    },

    // ---- chips ----------------------------------------------------------
    MuiChip: {
      styleOverrides: {
        root: {
          fontFamily: semibold,
          fontWeight: 600,
          fontSize: 12.5,
          letterSpacing: 0,
          height: 26,
          borderRadius: t.rSm,
          transition: transition,
          "&.Mui-focusVisible": focusRing,
        },
        label: {
          padding: "0 10px",
        },
        filled: {
          backgroundColor: t.surface2,
          color: t.ink,
        },
        outlined: {
          borderColor: t.line,
          color: t.ink,
        },
        colorPrimary: {
          backgroundColor: t.accentWeak,
          color: t.accent,
        },
        colorSuccess: {
          backgroundColor: t.surface2,
          color: t.up,
        },
        colorError: {
          backgroundColor: t.surface2,
          color: t.down,
        },
        deleteIcon: {
          fontSize: 15,
          color: t.ink3,
          "&:hover": { color: t.ink },
        },
      },
    },

    // ---- autocomplete ---------------------------------------------------
    MuiAutocomplete: {
      styleOverrides: {
        paper: {
          backgroundColor: t.surface,
          borderRadius: t.rMd,
          border: "1px solid " + t.line,
          boxShadow: float[8],
        },
        // the field keeps the 38px control height; the tags/input inside it
        // supply their own spacing
        inputRoot: {
          minHeight: t.ctrl,
          paddingTop: 0,
          paddingBottom: 0,
        },
        input: {
          height: 36,
          padding: "0 4px",
        },
        listbox: {
          fontFamily: regular,
          fontSize: 13.5,
          padding: 6,
        },
        option: {
          borderRadius: t.rSm,
          minHeight: 36,
          transition: transition,
          '&[aria-selected="true"]': {
            backgroundColor: t.accentWeak,
            color: t.accent,
          },
          '&.Mui-focused, &[data-focus="true"]': {
            backgroundColor: t.surface2,
          },
        },
        noOptions: {
          fontFamily: regular,
          fontSize: 13.5,
          color: t.ink3,
        },
        clearIndicator: {
          color: t.ink3,
        },
        popupIndicator: {
          color: t.ink3,
        },
      },
    },

    // ---- table ----------------------------------------------------------
    MuiTableContainer: {
      styleOverrides: {
        root: {
          backgroundColor: t.surface,
          borderRadius: t.rMd,
          boxShadow: "none",
          overflowX: "auto",
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          fontFamily: regular,
          fontSize: 13.5,
          color: t.ink,
          height: 52,
          padding: "0 16px",
          borderBottom: "1px solid " + t.line2,
          fontVariantNumeric: "tabular-nums",
        },
        head: {
          fontFamily: semibold,
          fontWeight: 600,
          fontSize: 11,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: t.ink3,
          backgroundColor: t.surface2,
          height: 40,
          borderBottom: "1px solid " + t.line,
          whiteSpace: "nowrap",
        },
        footer: {
          color: t.ink3,
          borderBottom: "none",
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          transition: transition,
          "&:hover > .MuiTableCell-body": {
            backgroundColor: t.surface2,
          },
          "&.Mui-selected, &.Mui-selected:hover": {
            backgroundColor: t.accentWeak,
            "& > .MuiTableCell-body": {
              backgroundColor: t.accentWeak,
            },
          },
          "&:last-child > .MuiTableCell-body": {
            borderBottom: "none",
          },
        },
      },
    },
    MuiTableSortLabel: {
      styleOverrides: {
        root: {
          color: t.ink3,
          "&:hover, &.Mui-active": { color: t.ink },
          "&.Mui-active .MuiTableSortLabel-icon": { color: t.ink },
          "&.Mui-focusVisible": focusRing,
        },
      },
    },
    MuiTablePagination: {
      styleOverrides: {
        root: {
          fontFamily: regular,
          fontSize: 12.5,
          color: t.ink3,
          borderTop: "1px solid " + t.line,
        },
        selectLabel: {
          fontSize: 12.5,
          color: t.ink3,
        },
        displayedRows: {
          fontSize: 12.5,
          color: t.ink3,
        },
      },
    },
  },
});

function App() {

    const [apiError, setApiError] = useState(false);
    // const ref = useRef(null);
    global.PageTopLoader = useRef(null);

    useEffect(() => {
        const cookies = new Cookies();
        const usertoken = cookies.get('session_token')
        const userid = cookies.get('session_userid')
        if(usertoken || userid){
            // console.log(usertoken);
            global.token = 'Token '+ usertoken;
        } else {
        }
        // setUsername(cookies.get('session_username'))
        // setUseremail(cookies.get('session_usermail'))

        const user = {
            'username': "test"
        };

        axios.post(global.apiurl + '/api/account/serviceauthenticate/', { user })
        .then(res => {
            // console.log(res.data, "test api");
            setApiError(false);
        }).catch(err => {
            setApiError(true);
            // console.log("Api Fail");
        });


    },[]);

    return (
      <div className="App h-100">
        <ToastContainer transition={Slide} />
        <LoadingBar color={t.accent} height={2} shadow={false} className="toploader" ref={global.PageTopLoader} />
        <ThemeProvider theme={theme}>
            <Router>
                { apiError === true ?
                  <Notfound pagetype="apiError" />
                :
                <Suspense fallback={<div className="d-flex justify-content-center align-items-center text-center h100vh"><div className="loading" /></div>}>
                <Switch>
                  {/* GLOBAL ROUTES STARTS */}
                  {/* The public marketing landing page. Login lives at /login.
                      PublicRoute, not Route: a logged-in user reaches "/" by
                      following a stale or deleted keyword link, and a plain
                      Route dropped them on the marketing site with four "Get
                      started" CTAs. PublicRoute sends them into the app. */}
                  <PublicRoute exact path="/" component={LandingPage} />
                  {/* THIS ROUTE MUST AVAILABLE FOR ALL USERS AND VISITORS FOR BOTH CASES LOGGED AND NOT LOGGED. */}
                  <PublicRoute path="/privacy-policy" component={PrivacyPolicy}/>
                  <PublicRoute path="/terms-and-conditions" component={TermsAndConditions}/>
                  <PublicRoute path="/login/reset" component={ForgotPassword} />
                  <PublicRoute path="/login/verify" component={ResetPassword} />
                  <PublicRoute path="/signup" component={Signup} />
                  <PublicRoute path="/register" component={Register} />
                  <PublicRoute path="/login" component={Login} />
                  {/* GLOBAL ROUTES ENDS */}
                  <PrivateRoute />
                </Switch>
                </Suspense>
                  }
            </Router>
        </ThemeProvider>
      </div>
    );
}

export default App;
