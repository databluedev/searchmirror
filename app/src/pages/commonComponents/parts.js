import React, { useState, useEffect } from "react";
import {
  Typography,
  TextField,
  InputLabel,
  Button,
  Select,
  MenuItem,
  IconButton,
  Autocomplete,
  Box,
  Skeleton,
  ListSubheader,
  styled,
} from "@mui/material";
import Tooltip from '@mui/material/Tooltip';

import InputAdornment from "@mui/material/InputAdornment";
import FilledInput from "@mui/material/FilledInput";
import OutlinedInput from "@mui/material/OutlinedInput";
import FormHelperText from "@mui/material/FormHelperText";
import { SelectDownArrow } from "../commonComponents/icons";

// Named for what they DRAW, not for the state they appear in. These were
// imported the other way round -- `Visibility` bound to invisible.svg -- which
// rendered correctly and read as a bug at every call site.
import EyeClosedIcon from "../../assets/images/invisible.svg";
import EyeOpenIcon from "../../assets/images/visible.svg";
import CountryFlag from "./country_flag";

// Every one of these controls used to hard-code the same DOM id, so MUI derived
// the same helper-text id for all of them and aria-describedby resolved to
// whichever error happened to come first in the document. Each instance now
// gets its own id, and the error text is wired to the control that owns it.
let fieldIdSeq = 0;
function useFieldId(providedId) {
  const [generated] = useState(() => {
    fieldIdSeq += 1;
    return "field-" + fieldIdSeq;
  });
  return providedId || generated;
}

const DownKR = (props) => {
  return (
    <>
      <div className="downArrow">
        <svg
          {...props}
          xmlns="http://www.w3.org/2000/svg"
          width="12.828"
          height="7.414"
          viewBox="0 0 12.828 7.414"
        >
          <path
            id="Path_380"
            data-name="Path 380"
            d="M0,5,5,0l5,5"
            transform="translate(11.414 6.414) rotate(180)"
            fill="none"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
          />
        </svg>
      </div>
    </>
  );
};
const Down = () => {
  return (
    <>
      <div className="downArrow">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="12.828"
          height="7.414"
          viewBox="0 0 12.828 7.414"
        >
          <path
            id="Path_380"
            data-name="Path 380"
            d="M0,5,5,0l5,5"
            transform="translate(11.414 6.414) rotate(180)"
            fill="none"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
          />
        </svg>
      </div>
    </>
  );
};
export function TitleLg({ children, ...props }) {
  return (
    <>
      <Typography
        className={props.class}
        variant="h1"
        component="h1"
        gutterBottom
      >
        {children}
      </Typography>
    </>
  );
}

export function Title({ children, ...props }) {
  return (
    <>
      <Typography
        variant="h2"
        component="div"
        gutterBottom
        className={props.class}
      >
        {children}
      </Typography>
    </>
  );
}
export function TextLg({ children, ...props }) {
  return (
    <>
      <Typography
        variant="p2"
        className={props.class}
        gutterBottom
        component="div"
      >
        {children}
      </Typography>
    </>
  );
}
export function Text({ children, ...props }) {
  return (
    <>
      <Typography
        variant="p"
        className={props.class}
        gutterBottom
        component="div"
      >
        {children}
      </Typography>
    </>
  );
}
export function SmallText({ children, ...props }) {
  return (
    <>
      <Typography
        variant="p1"
        component="div"
        className={props.class}
        gutterBottom
      >
        {children}
      </Typography>
    </>
  );
}
export function ParaLg({ children, ...props }) {
  return (
    <>
      <Typography
        variant="h3"
        component="div"
        className={props.class}
        gutterBottom
      >
        {children}
      </Typography>
    </>
  );
}
export function Para({ children, ...props }) {
  return (
    <>
      <Typography
        variant="h4"
        component="div"
        className={props.class}
        gutterBottom
        onClick={props.onclick}
      >
        {children}
      </Typography>
    </>
  );
}

const CssTextField = styled(TextField)({
  '& label.Mui-focused': {
    color: '#A0AAB4',
  },
  '& .MuiInput-underline:after': {
    borderBottomColor: '#B2BAC2',
  },
  '& .MuiOutlinedInput-root': {
    '& fieldset': {
      borderColor: '#E0E3E7',
    },
    '&:hover fieldset': {
      borderColor: '#E0E3E7',
    },
    '&.Mui-focused fieldset': {
      borderColor: '#E0E3E7',
    },
  },
});

/*{export function Input({ ...props }) {
  const [text, setText] = useState();
  return (
    <>
      <InputLabel shrink>{props.label}</InputLabel>
      <TextField
        error={text === ""}
        value={text}
        helperText={text === "" ? "Empty!" : null}
        id="outlined-basic"
        label=""
        variant="outlined"
        onChange={(event) => setText(event.target.value)}
        // onChange={props.onchange}
        onBlur={props.onchange}
        placeholder={props.placeholder}
        fullWidth
      />
    </>
  );
}

export function PasswordInput({ ...props }) {
  const [values, setValues] = React.useState({
    password: "",
  });

  const handleChange = (prop) => (event) => {
    setValues({ ...values, [prop]: event.target.value });
  };

  const handleClickShowPassword = () => {
    setValues({
      ...values,
      showPassword: !values.showPassword,
    });
  };

  const handleMouseDownPassword = (event) => {
    event.preventDefault();
  };
  return (
    <>
      <InputLabel shrink>{props.label}</InputLabel>
      <FilledInput
        autoFocus={true}
        placeholder={props.placeholder}
        className="passwordInput"
        // variant="outlined"
        fullWidth
        id="filled-adornment-password"
        error={true}
        type={values.showPassword ? "text" : "password"}
        value={values.password}
        helperText="Empty!" 
        onChange={handleChange("password")}
        disableUnderline={true}
        endAdornment={
          <InputAdornment position="end" className="eyeIcon">
            <span
              style={{ width: "14px", height: "19px" }}
              onClick={handleClickShowPassword}
              onMouseDown={handleMouseDownPassword}
            >
              {values.showPassword ? (
                <img src={EyeOpenIcon} alt="" />
              ) : (
                <img src={EyeClosedIcon} alt="" />
              )}
            </span>
          </InputAdornment>
        }
      />
       <FormHelperText className="Mui-error">Enter correct password</FormHelperText>
    </>
  );
}}*/
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: 200,
      marginTop: 5,
      boxShadow: "0px 2px 4px #00000029",
    },
  },
};
const KeyMenuProps = {
  PaperProps: {
    style: {
      maxHeight: 200,
      marginTop: 15,
      boxShadow: "0px 2px 4px #00000029",
    },
  },
};
// const names = [
//   "Oliver Hansen",
//   "Van Henry",
//   "April Tucker",
//   "Ralph Hubbard",
//   "Omar Alexander",
//   "Carlos Abbott",
//   "Miriam Wagner",
//   "Bradley Wilkerson",
//   "Virginia Andrews",
//   "Kelly Snyder",
// ];
/*{export function SelectMenu({ ...props }) {
  // const theme = useTheme();
  const [personName, setPersonName] = React.useState([]);

  const handleChange = (event) => {
    const {
      target: { value },
    } = event;
    setPersonName(
      // On autofill we get a stringified value.
      typeof value === "string" ? value.split(",") : value
    );
  };
  return (
    <>
      <InputLabel shrink className="mb-1">
        {props.label}
      </InputLabel>
      <Select
      error
        className="customSelect"
        displayEmpty
        value={personName}
        labelId="demo-simple-select-error-label"
        id="demo-simple-select-error"
        IconComponent={Down}
        onChange={handleChange}
        //  input={<OutlinedInput />}
        renderValue={(selected) => {
          if (selected.length === 0) {
            return <span className="placeText">Placeholder</span>;
          }

          return selected.join(", ");
        }}
        MenuProps={MenuProps}
        inputProps={{ "aria-label": "Without label" }}
      >
        {names.map((name) => (
          <MenuItem key={name} value={name}>
            {name}
          </MenuItem>
        ))}
      </Select>
      <FormHelperText className="Mui-error">Select the value</FormHelperText>
    </>
  );
}

export function AppButton({ children, ...props }) {
  const [loader, setLoader] = React.useState(false);

  const handleClick = () => {
    setLoader(true);
  };

  return (
    <>
      <Button
        variant="contained"
        color={props.color}
        fullWidth
        className={props.class}
        onClick={handleClick}
      >
        {loader ? (
          <span className="loading" />
        ) : (
          <>
            {" "}
            <span className={`d-flex m-r10 ${props.noIcon}`}>
              {props.Icon}
            </span>
            <span>{props.value}</span>
          </>
        )}
      </Button>
    </>
  );
}}*/

export function AppIconButton({ children, ...props }) {
  return (
    <>
      <IconButton
        className={props.class}
        variant="contained"
        color={props.color}
        onClick={props.onclick}
        // ref={props.ref}
        id={props.id}
        aria-controls={props.aria_controls}
        aria-expanded={props.aria_expanded}
        aria-haspopup={props.aria_haspopup}
        // docs/DESIGN.md, Button: "Icon-only buttons carry an aria-label."
        // The {...props} spread below is commented out, so callers passing
        // aria-label were silently rendering a nameless button.
        aria-label={props["aria-label"]}
      // {...props}
      >
        {props.Icon}
      </IconButton>
    </>
  );
}

export function AppTooltip(props) {
  return (
    <>
      <Tooltip classes={{ tooltip: props.className, popper: props.parentClassName }} title={props.title} placement={props.place}>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width={props.dimension || "11"}
          height={props.dimension || "11"}
          viewBox="0 0 11 11"
        >
          <path
            id="Path_49"
            data-name="Path 49"
            d="M7.5,2A5.5,5.5,0,1,0,13,7.5,5.5,5.5,0,0,0,7.5,2Zm0,8.25a.552.552,0,0,1-.55-.55V7.5a.55.55,0,1,1,1.1,0V9.7A.552.552,0,0,1,7.5,10.25Zm.55-4.4H6.95V4.75h1.1Z"
            transform="translate(-2 -2)"
            fill={props.color || "#b4aebe"}
          />
        </svg>
      </Tooltip>
    </>
  );
}


//

// export function OnelineTooltip({ children, ...props }) {
//   return (
//     <>
//       <Tooltip classes={{ tooltip: props.className }}  title={props.title} placement={props.placement}>
//         {children}
//       </Tooltip>
//     </>
//   );
// }


// export const HtmlTooltip = styled(({ className, ...props }) => (
//   <Tooltip {...props} classes={{ popper: className }} />
// ))(({ theme }) => ({
//   [`& .${tooltipClasses.tooltip}`]: {
//     backgroundColor: '#f5f5f9',
//     color: 'rgba(0, 0, 0, 0.87)',
//     maxWidth: 220,
//     fontSize: theme.typography.pxToRem(12),
//     border: '1px solid #dadde9',
//   },
// }));

export function NormalInput({ ...props }) {
  return (
    <>
      {props.nolabel ?
        <></>
        :
        <InputLabel shrink className={props.mb}>
          {props.label}
          <span className={props.spanclassname ? props.spanclassname : "spanClass"}>
            {props.span}
          </span>
        </InputLabel>
      }
      <CssTextField
        fontSize={props.fontsize}
        className={props.classname}
        multiline={props.multiline}
        style={{ whiteSpace: 'pre-wrap' }}
        type={props.type}
        error={props.error}
        value={props.value}
        name={props.name}
        autoComplete='off'
        autoFocus={props.autoFocus}
        helperText={props.errmsg}
        label=""
        disabled={props.disabled}
        inputProps={{ maxLength: props.maxlength }}
        onChange={props.onchange}
        onBlur={props.onblur}
        placeholder={props.placeholder}
        onKeyUp={props.onkeydown}
        fullWidth
        InputProps={
          props.endAdornment && { endAdornment: <InputAdornment position="end">{props.endAdornment}</InputAdornment> }
        }
        maxRows={props.maxrows}
        rows={props.rows}
      />
    </>
  )
}

export function RefInput({ children, ...props }) {
  return (
    <>
      {props.nolabel ?
        <></>
        :
        <InputLabel shrink className={props.mb}>
          {props.label}
          <span className={props.spanclassname ? props.spanclassname : "spanClass"}>
            {props.span}
          </span>
        </InputLabel>
      }
      {/* <input
        type={props.type}
        ref={props.ref}
        className={"w-100 customInput"}
        placeholder={props.placeholder}
        name={props.name}
        autoFocus={props.autoFocus}
        disabled={props.disabled}
      /> */}
      {children}
      {props.error ?
        <span className="redClr f12x" style={{ marginLeft: '5px', marginTop: '-3px' }}>
          {props.errmsg}
        </span>
        : null}
    </>
  )
}

export function Input({ ...props }) {
  const fieldId = useFieldId(props.id);
  return (
    <>
      {props.nolabel ?
        <></>
        :
        <InputLabel shrink className={props.mb} htmlFor={fieldId}>
          {props.label}
          <span className={props.spanclassname ? props.spanclassname : "spanClass"}>
            {props.span}
          </span>
        </InputLabel>
      }
      <TextField
        inputRef={props.ref}
        type={props.type}
        className={props.class}
        error={props.error}
        value={props.value}
        name={props.name}
        autoComplete={props.autoComplete || 'off'}
        autoFocus={props.autoFocus}
        helperText={props.errmsg}
        id={fieldId}
        label=""
        disabled={props.disabled}
        variant="outlined"
        inputProps={{ maxLength: props.maxlength }}
        // onChange={(event) => setText(event.target.value)}
        onChange={props.onchange}
        onBlur={props.onblur}
        placeholder={props.placeholder}
        onKeyUp={props.onkeydown}
        // helperText={props.helpertext}
        fullWidth
        // required
        InputProps={
          props.endAdornment && { endAdornment: <InputAdornment position="end">{props.endAdornment}</InputAdornment> }
        }
      />
    </>
  );
}

export const StyledArea = ({ ...props }) => {
  return (
    <>
      {props.nolable ?
        <></>
        :
        <InputLabel shrink className={props.mb}>
          {props.label}
          <span className={props.spanclassname ? props.spanclassname : "spanClass"}>
            {props.span}
          </span>
        </InputLabel>
      }
      <CssTextField
        style={{ whiteSpace: 'pre-wrap' }}
        disabled={props.disabled}
        helperText={props.errmsg}
        variant='outlined'
        fontSize={props.fontsize}
        multiline
        className={props.classname}
        error={props.error}
        value={props.value}
        name={props.name}
        autoComplete='off'
        autoFocus={props.autoFocus}
        id='outlined-basic'
        fullWidth
        onChange={props.onChange}
        placeholder={props.placeholder}
        maxRows={props.maxrows}
        rows={props.rows}
      // required
      />
    </>
  )
}
export const FileInput = ({ ...props }) => {
  return (
    <>
      {props.nolable ?
        <></>
        :
        <InputLabel shrink className={props.mb}>
          {props.label}
          <span className={props.spanclassname ? props.spanclassname : "spanClass"}>
            {props.span}
          </span>
        </InputLabel>
      }{props.imgSrc ?
        props.imgSrc.length > 0 ?
          <div class={props.imgCls}>
            <img alt="" srcSet={props.imgSrc} height={props.dm} />
          </div> : <></>
        : null
      }
      <div className="custom-file-upload">
        <input
          type='file'
          className={props.classname}
          value={props.value}
          name={props.name}
          onChange={props.onchange}
          autoComplete='off'
          autoFocus={props.autoFocus}
          placeholder={props.placeholder}
          accept="image/png, image/jpeg, image/jpg"
        // required
        />
      </div>
      {props.error ?
        <InputLabel shrink>
          <span style={{ 'color': 'red' }}>{props.errmsg}</span>
        </InputLabel>
        :
        <></>
      }
    </>
  )
}

export function PasswordInput({ ...props }) {
  const fieldId = useFieldId(props.id);
  const errorId = fieldId + "-error";
  const [values, setValues] = React.useState({
    password: "",
  });

  const handleClickShowPassword = () => {
    setValues({
      ...values,
      showPassword: !values.showPassword,
    });
  };

  const handleMouseDownPassword = (event) => {
    event.preventDefault();
  };
  return (
    <>
      <InputLabel shrink htmlFor={fieldId}>
        {props.label}
        <span className={props.spanclassname ? props.spanclassname : "spanClass"}>
          {props.span}
        </span>
      </InputLabel>
      <OutlinedInput
        inputProps={{
          maxLength: props.maxlength,
          "aria-describedby": props.error ? errorId : undefined,
        }}
        onKeyDown={props.onkeydown}
        autoComplete={props.autoComplete || "current-password"}
        placeholder={props.placeholder}
        className="passwordInput"
        fullWidth
        id={fieldId}
        error={props.error}
        type={values.showPassword ? "text" : "password"}
        value={props.value}
        // helperText={props.errmsg}
        onChange={props.onchange}
        onBlur={props.onblur}
        endAdornment={
          <InputAdornment position="end" className="eyeIcon">
            {/* `onlyIcon` is the opt-out _controls.scss already defines for a
                bare glyph. style.scss gives every .MuiIconButton-root a border
                and a filled background on hover, which turned this into a
                ringed circle hanging off the edge of the field. It is a glyph
                inside an input, not a button shell.

                The two assets are 14x12.088 and 14x9.545, so the box is fixed
                here: without it the field's contents shifted every time the
                control was toggled. */}
            <IconButton
              className="onlyIcon eyeIconButton"
              aria-label={values.showPassword ? "Hide password" : "Show password"}
              edge="end"
              size="small"
              disableRipple
              onClick={handleClickShowPassword}
              onMouseDown={handleMouseDownPassword}
            >
              {values.showPassword ? (
                <img src={EyeOpenIcon} alt="" />
              ) : (
                <img src={EyeClosedIcon} alt="" />
              )}
            </IconButton>
          </InputAdornment>
        }
      />
      {props.error ?
        <label className="error-msg" id={errorId}>{props.errmsg}</label>
        : null}
    </>
  );
}

export function CustomSelect({ ...props }) {
  const fieldId = useFieldId(props.id);
  const errorId = fieldId + "-error";
  return (
    <>
      <InputLabel shrink className="mb-1" id={fieldId + "-label"}>
        {props.label}<span className="spanClass redClr p-l5">{props.span}</span>
      </InputLabel>
      <Select
        disabled={props.disabled}
        error={props.error}
        className="customSelect"
        displayEmpty
        value={props.value}
        labelId={props.label ? fieldId + "-label" : undefined}
        id={fieldId}
        SelectDisplayProps={{
          "aria-invalid": props.error ? "true" : undefined,
          "aria-describedby": props.error ? errorId : undefined,
        }}
        IconComponent={Down}
        onChange={props.onchange}
        renderValue={(selected) => {
          if (selected === "" || selected === null || typeof selected === "undefined") {
            return <span className="placeText">{props.placeholder}</span>;
          }
          if (Array.isArray(selected)) {
            return selected.length ? selected.join(", ") : <span className="placeText">{props.placeholder}</span>;
          }
          const selectedRole = props.menulist.find((item) => item.rl_id === selected);
          return selectedRole ? selectedRole.rl : selected;
        }}
        MenuProps={MenuProps}
        inputProps={{ "aria-label": "Without label" }}
      >
        {props.menulist.length ?
          props.menulist.map((lst, i) => (
            <MenuItem key={i} value={lst.rl_id}>
              {lst.rl}
            </MenuItem>
          )) :
          // <MenuItem value="">
          //   <i className="darkgray">{props.nonSelect}</i>
          // </MenuItem>
          null
        }
        {/* <AppButton value="Create Role" class="white" noIcon="d-none" /> */}
        <div className="px-3 py-2">
          <Button variant="contained" onClick={props.handleTab} fullWidth>Create Role</Button>
        </div>
      </Select>
      {props.error ?
        <FormHelperText id={errorId} className="Mui-error">{props.errmsg}</FormHelperText>
        : null}
    </>
  )
}

export function SelectMenu({ ...props }) {
  const fieldId = useFieldId(props.id);
  const errorId = fieldId + "-error";

  return (
    <>
      <InputLabel shrink className="mb-1" id={fieldId + "-label"}>
        {props.label}<span className="spanClass">{props.span}</span>
      </InputLabel>
      <Select
        disabled={props.disabled}
        error={props.error}
        className="customSelect"
        displayEmpty
        value={props.value}
        labelId={props.label ? fieldId + "-label" : undefined}
        id={fieldId}
        SelectDisplayProps={{
          "aria-invalid": props.error ? "true" : undefined,
          "aria-describedby": props.error ? errorId : undefined,
        }}
        IconComponent={Down}
        onChange={props.onchange}
        renderValue={(selected) => {
          if (typeof (selected) === "string" ? selected.length === 0 : selected === 0) {
            return <span className="placeText">{props.placeholder}</span>;
          }

          return Array.isArray(selected) ? selected.join(", ") : selected;
        }}
        MenuProps={MenuProps}
        inputProps={{ "aria-label": "Without label" }}
      >
        {props.menulist.map((lst, i) => (
          <MenuItem key={i} value={lst}>
            {lst}
          </MenuItem>
        ))}
      </Select>
      {props.error ?
        <FormHelperText id={errorId} className="Mui-error">{props.errmsg}</FormHelperText>
        : null}
    </>
  );
}

export function SelectLang({ ...props }) {
  const fieldId = useFieldId(props.id);
  const errorId = fieldId + "-error";

  return (
    <>
      <InputLabel shrink className="mb-1" id={fieldId + "-label"}>
        {props.label}
      </InputLabel>
      <Select
        error={props.error}
        className="customSelect"
        displayEmpty
        value={props.value}
        labelId={props.label ? fieldId + "-label" : undefined}
        id={fieldId}
        SelectDisplayProps={{
          "aria-invalid": props.error ? "true" : undefined,
          "aria-describedby": props.error ? errorId : undefined,
        }}
        IconComponent={Down}
        onChange={props.onchange}
        renderValue={(selected) => {
          if (typeof (selected) === "string" ? selected.length === 0 : selected === 0) {
            return <span className="placeText">{props.placeholder}</span>;
          }

          return Array.isArray(selected) ? selected.join(", ") : selected;
        }}
        MenuProps={MenuProps}
        inputProps={{ "aria-label": "Without label" }}
      >
        {props.menulist.map((lst, i) => (
          <MenuItem key={i} value={lst.LN}>
            {lst.LN}
          </MenuItem>
        ))}
      </Select>
      {props.error ?
        <FormHelperText id={errorId} className="Mui-error">{props.errmsg}</FormHelperText>
        : null}
    </>
  );
}

export function AppButton({ children, ...props }) {
  return (
    <>
      <Button
        variant="contained"
        color={props.color}
        className={props.class}
        onClick={props.onclick}
        type={props.type}
        disabled={props.loading || props.disabled}
        id={props.id}
        fullWidth
      >
        {props.loading ? (
          <span className="loading" />
        ) : (
          <>
            {" "}
            <span className={`d-flex m-r10 ${props.noIcon}`}>
              {props.Icon}
            </span>
            <span>{props.value}</span>
          </>
        )}
      </Button>
    </>
  );
}

//
export function SelectRegion({ children, ...props }) {
  return (
    <Autocomplete
      id="country-select-demo"
      popupIcon={<SelectDownArrow />}
      options={props.menulist}
      // inputValue={region}
      // defaultValue={props.defaultvalue}
      // inputValue={"google.com (United States)"}
      autoHighlight
      getOptionLabel={(option) => option.RN + " (" + option.Rcnt + ")"}
      // getOptionLabel={(option) => option.Rcnt}
      onInputChange={(event, newInputValue) => props.onclear(newInputValue)}
      onChange={props.onchange}
      renderOption={(props, option) => (
        <Box
          component="li"
          sx={{ "& > img": { mr: 2, flexShrink: 0 } }}
          {...props}
          key={option.Rcd}
        >
          <CountryFlag
            style={{ borderRadius: "3px", marginTop: "2px" }}
            loading="lazy"
            width="24"
            height="16"
            code={option.Rcd}
            alt=""
          />
          {option.RN + " (" + option.Rcnt + ")"}
        </Box>
      )}
      renderInput={(params) => (
        <div style={{ position: "relative" }}>
          {(props.value && props.rgcode !== "") && (
            <span className="inputflag" >
              <CountryFlag
                style={{ borderRadius: "3px", marginTop: "2px" }}
                loading="lazy"
                width="24"
                height="16"
                code={props.rgcode}
                alt=""
              />
            </span>
          )}
          <TextField
            {...params}
            placeholder="Search"
            className={(props.value && props.rgcode !== "") ? "customSelect rgSelect" : "customSelect"}
            error={props.error}
            helperText={props.errmsg}
            inputProps={{
              ...params.inputProps,
              autoComplete: "off", // disable autocomplete and autofill
              // value: params.inputProps.value.RN
              value: props.value
            }}

          />
        </div>
      )}
    />
  );
}

//Serp Rank
export function Tsk({ children, ...props }) {
  return (
    <Skeleton
      className={props.className}
      sx={props.sx || { bgcolor: "var(--line)" }}
      variant="Text"
      width={props.width}
      height={props.height}
    />
  );
}

//Serp Rank
export function Rsk({ children, ...props }) {
  return (
    <Skeleton
      className={props.className}
      sx={props.sx || { bgcolor: "var(--line)" }}
      variant="rectangular"
      width={props.width}
      height={props.height || 18}
    />
  );
}

//Serp Rank
export function Csk({ children, ...props }) {
  return (
    <Skeleton
      className={props.className}
      sx={props.sx || { bgcolor: "var(--line)" }}
      variant="circular"
      width={props.width}
      height={props.height || 18}
    />
  );
}


export function SelectKeyword({ ...props }) {

  const fieldId = useFieldId(props.id);
  const errorId = fieldId + "-error";

  return (
    <>
      <Select
        error={props.error}
        className="customSelect keyDomSelect"
        displayEmpty
        value={props.value}
        id={fieldId}
        SelectDisplayProps={{
          "aria-invalid": props.error ? "true" : undefined,
          "aria-describedby": props.error ? errorId : undefined,
        }}
        IconComponent={DownKR}
        onChange={props.onchange}
        MenuProps={KeyMenuProps}
        inputProps={{ "aria-label": "Without label" }}
      >
        <MenuItem value={"keyword"}>Keyword</MenuItem>
        <MenuItem value={"domain"}>Domain</MenuItem>
      </Select>
      {props.error ?
        <FormHelperText id={errorId} className="Mui-error">{props.errmsg}</FormHelperText>
        : null}
    </>
  );
}

export function KRSelectRegion({ children, ...props }) {
  return (
    <Autocomplete
      id="country-select-demo"
      popupIcon={<SelectDownArrow />}
      options={props.menulist}
      // inputValue={region}
      // defaultValue={props.defaultvalue}
      // inputValue={"google.com (United States)"}
      autoHighlight
      getOptionLabel={(option) => option.RN + " (" + option.Rcnt + ")"}
      // getOptionLabel={(option) => option.Rcnt}
      onInputChange={(event, newInputValue) => props.onclear(newInputValue)}
      onChange={props.onchange}
      renderOption={(props, option) => (
        <Box
          component="li"
          sx={{ "& > img": { mr: 2, flexShrink: 0 } }}
          {...props}
          key={option.Rcd}
        >
          <CountryFlag
            style={{ borderRadius: "3px", marginTop: "2px" }}
            loading="lazy"
            width="24"
            height="16"
            code={option.Rcd}
            alt=""
          />
          {option.RN + " (" + option.Rcnt + ")"}
        </Box>
      )}
      renderInput={(params) => (
        <div style={{ position: "relative" }}>
          {(props.value && props.rgcode !== "") && (
            <span className="inputflag" >
              <CountryFlag
                style={{ borderRadius: "3px", marginTop: "2px" }}
                loading="lazy"
                width="24"
                height="16"
                code={props.rgcode}
                alt=""
              />
            </span>
          )}
          <TextField
            {...params}
            placeholder="Search"
            className={(props.value && props.rgcode !== "") ? "customSelect rgSelect" : "customSelect"}
            error={props.error}
            helperText={props.errmsg}
            inputProps={{
              ...params.inputProps,
              autoComplete: "off", // disable autocomplete and autofill
              // value: params.inputProps.value.RN
              value: props.value
            }}

          />
        </div>
      )}
    />
  );
}

export function NSelectMenu({ ...props }) {

  const fieldId = useFieldId(props.id);
  const errorId = fieldId + "-error";

  return (
    <>
      <InputLabel shrink className="mb-1" id={fieldId + "-label"}>
        {props.label}<span className="spanClass">{props.span}</span>
      </InputLabel>
      <Select
        error={props.error}
        className="customSelect"
        displayEmpty
        value={props.value}
        labelId={props.label ? fieldId + "-label" : undefined}
        id={fieldId}
        SelectDisplayProps={{
          "aria-invalid": props.error ? "true" : undefined,
          "aria-describedby": props.error ? errorId : undefined,
        }}
        IconComponent={props.disabled === true ? "" : Down}
        onChange={props.onchange}
        renderValue={(selected) => {
          if (typeof (selected) === "string" ? selected.length === 0 : selected === 0) {
            return <span className="placeText">{props.placeholder}</span>;
          }

          return selected;
        }}
        MenuProps={MenuProps}
        inputProps={{ "aria-label": "Without label" }}
        disabled={props.disabled === true ? true : false}
      >
        {props.menulist.map((lst, i) => (
          (props.currency !== "inr" || props.currency === "") ?
            <MenuItem key={i} value={lst}>
              {lst}
            </MenuItem>
            : null
        ))}
      </Select>
      {props.error ?
        <FormHelperText id={errorId} className="Mui-error">{props.errmsg}</FormHelperText>
        : null}
    </>
  );
}

export function KNRSelectRegion({ ...props }) {

  const fieldId = useFieldId(props.id);
  const errorId = fieldId + "-error";
  const [tablefullresult, setTblfulrslt] = useState({});

  useEffect(() => {
    setTblfulrslt(props.fullList)
  }, [props.fullList]);

  function listkwsearchFuc(e) {
    if (e.target.value !== "") {
      const filterDatas = tablefullresult.filter(
        item =>
          JSON.stringify(item.RN + " (" + item.Rcnt + ")")
            .toLowerCase()
            .indexOf(e.target.value.toLowerCase()) !== -1
      )
      props.regionUpdate(filterDatas);
    } else if (e.target.value === "") {
      props.regionUpdate(props.fullList);
    }

  }

  return (
    <>
      <Select
        error={props.error}
        className="customSelect rgnSelect"
        displayEmpty
        value={props.value}
        id={fieldId}
        SelectDisplayProps={{
          "aria-invalid": props.error ? "true" : undefined,
          "aria-describedby": props.error ? errorId : undefined,
        }}
        IconComponent={DownKR}
        onChange={props.onchange}
        onClose={props.menuOpen}
        MenuProps={{ classes: { paper: props.className }, autoFocus: false }}
        inputProps={{ "aria-label": "Without label" }}
        renderValue={(s) => {
          // No {...props} spread here: this Box renders a <div>, so every
          // custom prop (regionUpdate, menuOpen, fullList, menulist, rgname,
          // rgcnt) leaked onto the DOM and React warned about each one. The
          // only two attributes it needs are set explicitly below anyway.
          return <Box
            sx={{ "& > img": { mr: 2, flexShrink: 0 } }}
            key={props.rgcode}
            className={props.rgName}
          >
            <CountryFlag
              style={{ borderRadius: "3px", marginTop: "2px" }}
              loading="lazy"
              width="24"
              height="16"
              code={props.rgcode}
              alt=""
              className="rgrndrImg m-r10"
            />
            <span>{props.rgname + " (" + props.rgcnt + ")"}</span>
          </Box>
        }}
      >
        <div className="m-t10">
          <ListSubheader>
            <TextField
              autoFocus
              className="search"
              id="outlined-basic"
              label=""
              variant="outlined"
              fullWidth
              placeholder="Search"
              onChange={listkwsearchFuc}
              // onKeyPress={listkwsearchFuc}
              autoComplete="off"
              classes={{ clearIndicator: { color: "red" } }}
              onKeyDown={(e) => {
                if (e.key !== "Escape") {
                  // Prevents autoselecting item while typing (default Select behaviour)
                  e.stopPropagation();
                }
              }}
            />
          </ListSubheader>
        </div>
        {props.menulist.length > 0 ?
          props.menulist.map((lst, i) => (
            <MenuItem key={i} value={lst.Rcd + " " + lst.RN + " (" + lst.Rcnt + ")"}>
              <CountryFlag
                style={{ borderRadius: "3px", marginTop: "2px" }}
                loading="lazy"
                width="24"
                height="16"
                code={lst.Rcd}
                alt=""
                className="m-r10"
              />
              <span className="rgnName">{lst.RN + " (" + lst.Rcnt + ")"}</span>
            </MenuItem>
          ))
          :
          <span className="noOptn">No options</span>
        }
      </Select>
      {props.error ?
        <FormHelperText id={errorId} className="Mui-error">{props.errmsg}</FormHelperText>
        : null}
    </>
  );
}

// PAGE AUDIT STARTS //

export function PageAuditModalSearch({ ...props }) {

  const [menulist, setMenuList] = useState({});
  const [primaryKeyword, setPrimaryKeyword] = React.useState('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    setMenuList(props.skeywords)
    setPrimaryKeyword(props.primaryKeyword);
  }, [props.skeywords, props.primaryKeyword]);

  const getFilteredData = () => {
    if (searchTerm === '') {
      return menulist;
    }
    return menulist.length > 0 && menulist.filter(item => item.kw_name.toLowerCase().includes(searchTerm.toLowerCase()));
  };

  const handleSearch = (event) => {
    setSearchTerm(event.target.value);
  };

  return (
    <>
      <Select
        className="customSelect rgnSelect"
        displayEmpty
        value={primaryKeyword}
        labelId="demo-simple-select-error-label"
        id="demo-simple-select-error"
        IconComponent={DownKR}
        onChange={props.selectPrimaryKeyword}
        MenuProps={{ classes: { paper: props.className }, autoFocus: false }}
        inputProps={{ "aria-label": "Without label" }}
        renderValue={(selected) => {
          if (!selected) {
            return <MenuItem key="default" value=""> Choose the primary keyword.</MenuItem>;
          } else {
            const selectedElement = getFilteredData().find(item => item.kw_id === selected);
            return selectedElement ? <MenuItem key="selected" value={selectedElement.kw_id}><span className="rgnName">{selectedElement.kw_name}</span></MenuItem> : <MenuItem key="default" value=""> Choose the primary keyword.</MenuItem>;
          }
        }}
      >
        <div className="m-t10">
          <ListSubheader>
            <TextField
              autoFocus
              className="search"
              id="outlined-basic"
              label=""
              variant="outlined"
              fullWidth
              placeholder="Search"
              onChange={handleSearch}
              onKeyPress={handleSearch}
              autoComplete="off"
              classes={{ clearIndicator: { color: "red" } }}
              onKeyDown={(e) => {
                if (e.key !== "Escape") {
                  // Prevents autoselecting item while typing (default Select behaviour)
                  e.stopPropagation();
                }
              }}
            />
          </ListSubheader>
        </div>

        {getFilteredData().length > 0 && getFilteredData().map((eachKeyword, index) => (
          <MenuItem key={index} value={eachKeyword.kw_id}><span className="rgnName">{eachKeyword.kw_name}</span></MenuItem>
        ))}

        {/* {props.menulist.length >0 ?
           props.menulist.map((lst, i) => (
              <MenuItem key={i} value={lst.Rcd + " " + lst.RN + " (" +lst.Rcnt+ ")"}>
                 <CountryFlag
                    style={{ borderRadius: "3px", marginTop: "2px" }}
                    loading="lazy"
                    width="24"
                    height="16"
                    code={lst.Rcd}
                    alt=""
                    className="m-r10"
                 />
                 <span className="rgnName">{lst.RN + " (" +lst.Rcnt+ ")"}</span>
              </MenuItem>
           ))
        :
        <span className="noOptn">No options</span>
        } */}
      </Select>
      {/* {props.error ?
        <FormHelperText className="Mui-error">{props.errmsg}</FormHelperText>
        : null} */}
    </>
  );
}

export function AppSmallButton({ children, ...props }) {
  return (
    <>
      <Button
        variant="contained"
        color={props.color}
        className={props.class}
        onClick={props.onclick}
        type={props.type}
        disabled={props.loading}
        size={props.size}
        id={props.id}
        fullWidth
      >
        {props.loading ? (
          <span className="loading" />
        ) : (
          <>
            {" "}
            <span className={`d-flex m-r10 ${props.noIcon}`}>
              {props.Icon}
            </span>
            <span>{props.value}</span>
          </>
        )}
      </Button>
    </>
  );
}

// PAGE AUDIT ENDS //
export function CGARemapModalSearch({ ...props }) {

  const [menulist, setMenuList] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [sourceURL, setSourceURL] = useState('');

  useEffect(() => {
    setMenuList(props.competitorURLs)
    setSourceURL(props.selectedRows.source_url)
  }, [props.competitorURLs, props.selectedRows, props.searching]);

  const getFilteredData = () => {
    if (searchTerm === '') {
      return menulist;
    }
    return menulist.length > 0 && menulist.filter(item => item.source_url.includes(searchTerm));
  };

  const handleSearch = (event) => {
    let searchText = event.target.value
    setSearchTerm(event.target.value);
    if (parseInt(searchText.length % 3) === 0) {
      setMenuList([])
      props.handleNewSearch(searchText)
    }
  };

  const handleChange = (event) => {
    props.setRemapURL(event.target.value)
  }

  return (
    <>
      <div className="mt-2">
        <TextField
          autoFocus
          className="search"
          id="outlined-basic"
          variant="outlined"
          fullWidth
          placeholder="Search"
          autoComplete="off"
          classes={{ clearIndicator: { color: "red" } }}
          value={props.selectedRows.source_url && props.selectedRows.source_url}
          disabled
        />
      </div>
      <div className="mt-2">
        <Select
          className="customSelect rgnSelect"
          displayEmpty
          value={props.selectedRows.domain_url_id && props.selectedRows.domain_url_id}
          labelId="demo-simple-select-error-label"
          id="demo-simple-select-error"
          IconComponent={DownKR}
          onChange={handleChange}
          MenuProps={{ classes: { paper: props.className }, autoFocus: false }}
          inputProps={{ "aria-label": "Without label" }}
          renderValue={(selected) => {
            if (!selected) {
              return <MenuItem key="default" value=""> Choose the Competitor URL.</MenuItem>;
            } else {

              const filteredData = getFilteredData();
              const selectedElement = Array.isArray(filteredData) ? filteredData.find(item => item.domain_url_id === selected) : null;
              return selectedElement ? <MenuItem key="selected" value={selectedElement.domain_url_id}><span className="rgnName">{selectedElement.source_url}</span></MenuItem> : <MenuItem key="default" value=""> Choose the primary keyword.</MenuItem>;
            }
          }}
        >

          <div className="m-t10">
            <ListSubheader>
              <TextField
                autoFocus
                className="search"
                id="outlined-basic"
                label=""
                variant="outlined"
                fullWidth
                placeholder="Search"
                onChange={handleSearch}
                autoComplete="off"
                classes={{ clearIndicator: { color: "red" } }}
                onKeyDown={(e) => {
                  if (e.key !== "Escape") {
                    // Prevents autoselecting item while typing (default Select behaviour)
                    e.stopPropagation();
                  }
                }}
              />
            </ListSubheader>
          </div>
          {
            getFilteredData().length > 0 ? getFilteredData().map((eachKeyword, index) => (
              <MenuItem key={index} value={eachKeyword.domain_url_id} sx={{ maxWidth: "600px" }}><span className="rgnName">{eachKeyword.source_url}</span></MenuItem>
            )) :
              (props.searching) ? <div className="m-t2"><MenuItem><Tsk width={600} /></MenuItem></div>
                : <div className="d-flex m-t10 justify-content-center"><Para className="wd-history-sub-title mb-0">No Data Found!
                </Para></div>
          }
        </Select>
      </div >
    </>
  );
}
