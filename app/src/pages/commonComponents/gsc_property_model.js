function GSCPropertyModel(props) {
    return (
        <div className="propertyMdlBxColor">
            {props.gscdata &&
                <div className="propertyCount my-3 overflow-auto" style={{ 'maxHeight': '250px' }}>
                    {props.gscdata.length > 0 ? props.gscdata.map((propertyItem, propertyIndex) => (
                        <div key={propertyItem}>
                            <ul className="px-4" key={propertyIndex}>
                                <div onClick={() => props.handleGSCPropertySelect(propertyItem)} className="rounded cursorP propertyBrdrColor my-2 py-3 px-3 d-flex justify-content-between prBox f15x" key={propertyIndex}>
                                    <div className="text-truncate ">{propertyItem}</div>
                                </div>
                            </ul>
                        </div>
                    ))
                        :
                        <div className="text-center" style={{ color: 'var(--ink-3)' }}>No Properties</div>
                    }
                </div>
            }
        </div>
    )
}
export default GSCPropertyModel