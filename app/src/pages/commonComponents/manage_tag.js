import { WithContext as ReactTags } from 'react-tag-input';
import { toast } from 'react-toastify';
import { CloseIcon } from "../commonComponents/icons";
import { fstLtrCapitalfun } from "../common_fun";

const separators = [",", "Enter"];


export const FullPageTagInput = (props) => {

  const handleAddition = (tag1) => {
    var tag = tag1.text.toLowerCase();
    // var objs = {}

    if (tag.trim() !== "") {
      if (Number(Object.keys(props.selectedtags).length) < 20) {
        if (/^[a-zA-Z0-9 ]+$/.test(tag)) {
          if (props.selectedtags.filter(e => e.toLowerCase() === tag).length === 0) {
            // if(this.state.othertags.filter(item => item === tag).length === 0){
            //     objs = { id:"new" ,text:tag };
            // }else{
            //     objs = { id:"old" ,text:tag };
            // }
            // objs = { id:tag ,text:tag };
            var selecttag = [tag, ...props.selectedtags]
            props.tagupdatefun(selecttag)
            if (props.othertags.includes(tag)) {
              var ottag = [...props.othertg.filter((intag, index) => intag !== tag)];
              props.othertagupdatefun(ottag)
            }
            // setSelectedtags([...selectedtags, tag]);
            // this.setState({
            //     othertags:this.state.othertags.filter(item => item !== tag),
            // });
          } else {
            toast.error('The tag is already added.')
          }
        } else {
          toast.error("Special characters are not allowed")
        }
      } else {
        toast.error("Maximum 20 tags only allowed")
      }
    }
  }

  const handleInputBlur = (tag) => {
    var obj = { id: 'new', text: tag };
    handleAddition(obj)
  }

  const handleDelete = (tag) => {
    var selecttag = [...props.selectedtags.filter((intag, index) => intag !== tag)];
    props.tagupdatefun(selecttag)
    if (props.othertags.includes(tag)) {
      var otag = [tag, ...props.othertg]
      props.othertagupdatefun(otag)
    }
  };

  const handleCommontag = (tag) => {
    var commontag = [...props.cmntags.filter((intag, index) => intag !== tag)];
    props.cmntagupdatefun(commontag)
    if (props.othertags.includes(tag)) {
      var otag = [tag, ...props.othertg]
      props.othertagupdatefun(otag)
    }
  };

  const addtag = (tag) => {
    var obj = { id: 'old', text: tag }
    handleAddition(obj)
  }

  return (
    <div className="tags-input keyword">
      <div className="tag-input-box">
        <ReactTags
          autoFocus={true}
          separators={separators}
          handleAddition={handleAddition}
          handleInputBlur={handleInputBlur}
          allowDeleteFromEmptyInput={false}
          allowAdditionFromPaste={false}
          allowUnique={false}
          allowDragDrop={false}
          maxLength={25}
          inputFieldPosition="top"
          placeholder="Use comma or press enter to separate your tags"
        />

        <ul className="m-t20">
          {props.selectedtags.map((tag, index) => (
            <li className="tagChip tagChip--on" key={index}>
              <span>{fstLtrCapitalfun(tag)}</span>
              <button type="button" className="close" aria-label={`Remove ${tag} tag`} onClick={() => handleDelete(tag)}>
                <CloseIcon color="currentColor" />
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="m-t20 maxh220x overflow-y-auto">
        {props.cmntags && props.cmntags.length > 0 ?
          <>
            <div className="fB f16x mb-3">Common Tags in this Project</div>

            <ul className="">
              {props.cmntags.map((tag, index) => (
                <li key={index} className="">
                  <span className="">{fstLtrCapitalfun(tag)}</span>
                  <button type="button" className="close" aria-label={`Remove ${tag} tag`} onClick={() => handleCommontag(tag)}>
                    <CloseIcon />
                  </button>
                </li>
              ))}
            </ul>
          </>
          : null}

        {props.othertg.length > 0 ?
          <>
            <div className="fB f16x mb-3 mt-4">Other Tags in this Project</div>

            <ul className="">
              {props.othertg.map((tag, index) => (
                <li key={index} className="cursorP" onClick={() => addtag(tag)}>
                  <span className="p-r10">{fstLtrCapitalfun(tag)}</span>
                </li>
              ))}
            </ul>
          </>
          : null}
      </div>
    </div>
  );
};


export const TagsInput = (props) => {

  const handleAddition = (tag1) => {
    var tag = tag1.text.toLowerCase();
    // var objs = {}

    if (tag.trim() !== "") {
      if (Number(Object.keys(props.selectedtags).length) < 20) {
        if (/^[a-zA-Z0-9 ]+$/.test(tag)) {
          if (props.selectedtags.filter(e => e.toLowerCase() === tag).length === 0) {
            // if(this.state.othertags.filter(item => item === tag).length === 0){
            //     objs = { id:"new" ,text:tag };
            // }else{
            //     objs = { id:"old" ,text:tag };
            // }
            // objs = { id:tag ,text:tag };
            var selecttag = [tag, ...props.selectedtags]
            props.tagupdatefun(selecttag)
            if (props.othertags.includes(tag)) {
              var ottag = [...props.othertg.filter((intag, index) => intag !== tag)];
              props.othertagupdatefun(ottag)
            }
            // setSelectedtags([...selectedtags, tag]);
            // this.setState({
            //     othertags:this.state.othertags.filter(item => item !== tag),
            // });
          } else {
            toast.error('The tag is already added.')
          }
        } else {
          toast.error("Special characters are not allowed")
        }
      } else {
        toast.error("Maximum 20 tags only allowed")
      }
    }
  }

  const handleInputBlur = (tag) => {
    var obj = { id: 'new', text: tag };
    handleAddition(obj)
  }

  const handleDelete = (tag) => {
    var selecttag = [...props.selectedtags.filter((intag, index) => intag !== tag)];
    props.tagupdatefun(selecttag)
    if (props.othertags.includes(tag)) {
      var otag = [tag, ...props.othertg]
      props.othertagupdatefun(otag)
    }
  };

  const addtag = (tag) => {
    var obj = { id: 'old', text: tag }
    handleAddition(obj)

  }

  return (
    <div className="tags-input keyword">
      <ReactTags
        autoFocus={false}
        separators={separators}
        handleAddition={handleAddition}
        handleInputBlur={handleInputBlur}
        allowDeleteFromEmptyInput={false}
        allowAdditionFromPaste={false}
        allowUnique={false}
        allowDragDrop={false}
        maxLength={25}
        inputFieldPosition="top"
        placeholder="Use comma or press enter to separate your tags"
      />
      <ul className={props.othertg.length > 3 ? "maxh140x overflow-y-auto" : ""}>
        {props.selectedtags.map((tag, index) => (
          <li key={index}>
            <span>{fstLtrCapitalfun(tag)}</span>
            <button type="button" className="close" aria-label={`Remove ${tag} tag`} onClick={() => handleDelete(tag)}>
              <CloseIcon />
            </button>
          </li>
        ))}
      </ul>
      {props.othertg.length > 0 ?
        <>
          <div className="fM f-md mb-3 mt-4">OTHER TAGS IN THIS PROJECT</div>

          <ul className={(props.selectedtags.length > 3 || props.othertg.length > 6) ? "maxh140x overflow-y-auto" : ""}>
            {props.othertg.map((tag, index) => (
              <li key={index} className="cursorP" onClick={() => addtag(tag)}>
                <span className="p-r10">{fstLtrCapitalfun(tag)}</span>
              </li>
            ))}
          </ul>
        </>
        : null}
    </div>
  );
};


export const KeywordInput = (props) => {




  const handleAddition = (tag1) => {
    var word = tag1.text
    var selecttag = null;
    var msg = null;
    var limitLeft = Number(Object.keys(props.selectedtags).length) - props.limit
    if (word.includes(',')) {
      if (Number(Object.keys(props.selectedtags).length) < props.limit) {
        var keyArr = word.split(',').filter(s => s.trim());
        const keyArrDuplicates = [...new Set(keyArr)];
        // Remove keywords already existing
        var newArr = keyArrDuplicates.filter(val => !props.selectedtags.includes(val));
        if (newArr.length > limitLeft) {
          // Remove last elements based onlimit left
          newArr.splice(newArr.length - limitLeft, limitLeft);
          selecttag = [...newArr, ...props.selectedtags]
          props.tagupdatefun(selecttag)
        } else {
          selecttag = [...newArr, ...props.selectedtags]
          props.tagupdatefun(selecttag)
        }
      } else {
        msg = "You have reached the maximum number of keywords entered."
        toast.error(msg)
      }
    }
    else {
      var tag = tag1.text.toLowerCase();
      if (tag.trim() !== "") {
        if (Number(Object.keys(props.selectedtags).length) < props.limit) {
          if (props.selectedtags.filter(e => e.toLowerCase() === tag).length === 0) {
            // if(this.state.othertags.filter(item => item === tag).length === 0){
            //     objs = { id:"new" ,text:tag };
            // }else{
            //     objs = { id:"old" ,text:tag };
            // }
            // objs = { id:tag ,text:tag };
            selecttag = [tag, ...props.selectedtags]
            props.tagupdatefun(selecttag)
            // setSelectedtags([...selectedtags, tag]);
            // this.setState({
            //     othertags:this.state.othertags.filter(item => item !== tag),
            // });
          } else {
            toast.error('The keyword is already added.')
          }
        } else {
          // var msg = "Maximum "+ props.limit.toString() +" keywords only allowed"
          msg = "You have reached the maximum number of keywords entered."
          toast.error(msg)
        }
      }
    }
  }

  // const handleAddition = (tag1) => {
  //     var tag = tag1.text.toLowerCase();
  //     // var objs = {}

  //     if (tag.trim() !== ""){
  //         if(Number(Object.keys(props.selectedtags).length) < props.limit ){
  //             if (props.selectedtags.filter(e => e.toLowerCase() === tag).length === 0) {
  //                 // if(this.state.othertags.filter(item => item === tag).length === 0){
  //                 //     objs = { id:"new" ,text:tag };
  //                 // }else{
  //                 //     objs = { id:"old" ,text:tag };
  //                 // }
  //                 // objs = { id:tag ,text:tag };
  //                 var selecttag = [tag,...props.selectedtags]
  //                 props.tagupdatefun(selecttag)
  //                 // setSelectedtags([...selectedtags, tag]);
  //                 // this.setState({
  //                 //     othertags:this.state.othertags.filter(item => item !== tag),
  //                 // });
  //             }else{
  //                 toast.error('The keyword is already added.')
  //             }
  //         }else {
  //             // var msg = "Maximum "+ props.limit.toString() +" keywords only allowed"
  //             var msg = "You have reached the maximum number of keywords entered."
  //             toast.error(msg)
  //         }
  //     }
  // }

  const handleInputBlur = (tag) => {
    var obj = { id: 'new', text: tag };
    handleAddition(obj)
  }

  const handleChange = (tag) => {
    // console.log("tag...", tag)
  }

  return (
    <div className="tags-input keyword">
      <ReactTags
        // tags={selectedtags} 
        autoFocus={true}
        // suggestions={suggestions }
        separators={separators}
        // handleDelete={handleDelete}
        handleAddition={handleAddition}
        handleInputChange={handleChange}
        handleInputBlur={handleInputBlur}
        allowDeleteFromEmptyInput={false}
        allowAdditionFromPaste={false}
        allowUnique={false}
        allowDragDrop={false}
        // maxLength={25}
        inputFieldPosition="top"
        placeholder="Use comma or press enter to separate your keywords"
        // The tag input is the field a failed "add at least one keyword"
        // points at, so it has to announce itself as the invalid one.
        inputProps={{
          "aria-invalid": props.invalid ? "true" : undefined,
          "aria-describedby": props.invalid ? props.errorid : undefined,
        }}
      />
    </div>
  );
};

export const BrandKeywordInput = (props) => {

  const handleAddition = (tag1) => {
    var tag = tag1.text.toLowerCase();
    if (tag.trim() !== "") {
      if (Number(Object.keys(props.selectedtags).length) < 5) {
        if (/^[\u0621-\u064A\u0660-\u0669a-zA-Z0-9 ]+$/.test(tag)) {
          if (props.selectedtags.filter(e => e.toLowerCase() === tag).length === 0) {
            var selecttag = [tag, ...props.selectedtags]
            props.tagupdatefun(selecttag)
            if (props.othertags.includes(tag)) {
              var ottag = [...props.othertg.filter((intag, index) => intag !== tag)];
              props.othertagupdatefun(ottag)
            }
          } else {
            toast.error('The keyword is already added.')
          }
        } else {
          toast.error("Special characters are not allowed")
        }
      } else {
        toast.error("Maximum 5 keywords only allowed")
      }
    }
  }

  const handleInputBlur = (tag) => {
    var obj = { id: 'new', text: tag };
    handleAddition(obj)
  }

  const handleDelete = (tag) => {
    var selecttag = [...props.selectedtags.filter((intag, index) => intag !== tag)];
    props.tagupdatefun(selecttag)
    if (props.othertags.includes(tag)) {
      var otag = [tag, ...props.othertg]
      props.othertagupdatefun(otag)
    }
  };

  const addtag = (tag) => {
    var obj = { id: 'old', text: tag }
    handleAddition(obj)

  }

  return (
    <div className="tags-input keyword">
      <ReactTags
        autoFocus={false}
        separators={separators}
        handleAddition={handleAddition}
        handleInputBlur={handleInputBlur}
        allowDeleteFromEmptyInput={false}
        allowAdditionFromPaste={false}
        allowUnique={false}
        allowDragDrop={false}
        maxLength={100}
        inputFieldPosition="top"
        placeholder="Enter your branded keywords"
      />
      <ul className={props.othertg.length > 3 ? "maxh140x overflow-y-auto" : ""}>
        {props.selectedtags.map((tag, index) => (
          <li key={index}>
            <span>{fstLtrCapitalfun(tag)}</span>
            <button type="button" className="close" aria-label={`Remove ${tag} tag`} onClick={() => handleDelete(tag)}>
              <CloseIcon />
            </button>
          </li>
        ))}
      </ul>
      {props.othertg.length > 0 ?
        <>
          <div className="fM f-md mb-3 mt-4">OTHER TAGS IN THIS PROJECT</div>

          <ul className={(props.selectedtags.length > 3 || props.othertg.length > 6) ? "maxh140x overflow-y-auto" : ""}>
            {props.othertg.map((tag, index) => (
              <li key={index} className="cursorP" onClick={() => addtag(tag)}>
                <span className="p-r10">{fstLtrCapitalfun(tag)}</span>
              </li>
            ))}
          </ul>
        </>
        : null}
    </div>
  );
};
