import React from 'react';
import clsx from 'clsx';
import { makeStyles } from '@material-ui/core/styles';
import IconButton from '@material-ui/core/IconButton';
import InputAdornment from '@material-ui/core/InputAdornment';
import TextField from '@material-ui/core/TextField';
import MenuItem from '@material-ui/core/MenuItem';
import Visibility from '@material-ui/icons/Visibility';
import VisibilityOff from '@material-ui/icons/VisibilityOff';
import Input from '@material-ui/core/Input';
import OutlinedInput from '@material-ui/core/OutlinedInput';
import FilledInput from '@material-ui/core/FilledInput';
import InputLabel from '@material-ui/core/InputLabel';
import FormHelperText from '@material-ui/core/FormHelperText';
import FormGroup from '@material-ui/core/FormGroup';
import FormControl from '@material-ui/core/FormControl';
import Select from '@material-ui/core/Select';
import Button from '@material-ui/core/Button';
import CircularProgress from '@material-ui/core/CircularProgress';
import Typography from '@material-ui/core/Typography';
import Next from '../fractions/NextButton'

const useStyles = makeStyles(theme => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
    flexDirection: 'column',
    width: "80%",
    margin: "auto",
  },
  margin: {
    margin: theme.spacing(1),
  },
  textField: {
    flexBasis: 100,
    flexGrow: 1,
  },
  inputGroup: {
    display: "flex",
    flexDirection: "row",
    flexBasis: 150,
  },
  formControl: {
    flexGrow: 3,
    margin: "5px",
  },
  outputFormControl: {
    display: "flex",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
  },
  progress: {
    margin: '5px',
  },
  title: {
    margin: '8px',
    color: '#616161',
  },
  nextButton: {
    float: 'right',
  },
  directions: {
    width: '100%',
  }
}));

const SelectComponent = (props) => {
  const classes = useStyles();
  const {
    value,
    onChange,
    attributes,
    inputName,
    inputId,
    filterFunction,
    inputLabel,
    error,
    helperText,
  } = props
  return <FormControl className={classes.formControl} error={error}>
    <InputLabel htmlFor="sort-by-attribute">{inputLabel}</InputLabel>
    <Select
      disabled={attributes.length <= 0}
      value={value}
      onChange={onChange}
      inputProps={{
        name: inputName,
        id: inputId,
      }}
    >
      <MenuItem value="">
        <em>Empty!</em>
      </MenuItem>
      {
        attributes
          .filter(attr => filterFunction(attr))
          .map(attr => (
            <MenuItem key={attr.id} value={attr.attribute}>{attr.attribute}</MenuItem>
          ))
      }

    </Select>
    <FormHelperText>{helperText}</FormHelperText>
  </FormControl>
}

export default function OutlinedInputAdornments(props) {
  const classes = useStyles();
  const {
    selectedResource,
    resourceSelectDialogOpen,
    attributes,
    sortByChange,
    sortByFilter,
    sortByValue,
    groupByChange,
    groupByFilter,
    groupByValue,
    error,
    next,
    skip,
    validateSelectedResource,
    getLineFeatures,
  } = props
  const onNext = () => {
    if (!selectedResource) validateSelectedResource(true)
    else{
      if (groupByValue.length == 0 && sortByValue.length == 0) skip()
      else {
        next()
        getLineFeatures()
      }
    }
  }
  return (
    <div className={classes.root}>
      <Typography variant="subtitle1" className={classes.title}>Select Point Layer:</Typography>
      <TextField
        error={error}
        className={clsx(classes.margin, classes.textField)}
        variant="outlined"
        label="Input Layer Name"
        value={selectedResource && selectedResource.title || ''}
        InputProps={{
          startAdornment: <InputAdornment position="start"> </InputAdornment>,
          onClick: resourceSelectDialogOpen,
          placeholder: 'Input Layer Name'
        }}
        helperText={'Please Select Layer'}
      />
      <div className={classes.inputGroup}>
        <SelectComponent
          value={sortByValue}
          onChange={sortByChange}
          attributes={attributes}
          filterFunction={sortByFilter}
          inputName={"sortByValue"}
          inputId={"sort-by-attribute"}
          inputLabel={"Sort By"}
          helperText={'Please Select Attribute'}
        />
        <SelectComponent
          attributes={attributes}
          value={groupByValue}
          onChange={groupByChange}
          filterFunction={groupByFilter}
          inputName={"groupByValue"}
          inputId={"group-by-attribute"}
          inputLabel={"Group By"}
          helperText={'Please Select Attribute'}
        />
      </div>
      <div className={classes.directions}>
        <Next
          next={true}
          className={classes.nextButton}
          onClick={onNext}
        />
      </div>
    </div>
  );
}
