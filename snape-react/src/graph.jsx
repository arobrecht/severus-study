import ReactEChartsCore from "echarts-for-react";
import echarts from "echarts/lib/echarts";
import "echarts/lib/chart/graph";
import { node_coordinates_dict, color_dict, curveness_dict } from './graph_settings';


/**
 * Creates graph object (links, nodes, categories). Takes the pre created nodes and links from experiment.tsx and updates
 * the current triple in links and nodes with opacity=1.
 *
 * @param blocks
 * @param currentBlock
 * @param currentTriples
 * @param links
 * @param nodes
 * @returns {{nodes_g: unknown[], categories_g: *[], links_g: unknown[]}}
 */
function createGraph(blocks, currentBlock, currentTriples, links, nodes) {
   //  javascripts default is copy by reference
   let nodes_cloned = structuredClone(nodes);
   let links_cloned = structuredClone(links);

   for (let i=0; i<currentTriples.length; i++) {
       let currentSplit = currentTriples[i].split(",");
            let triple_text = currentSplit[0].concat(",", currentSplit[2])
                .replace(",", "-")
                .replaceAll("QO.", "")
                .replace("(", "")
                .replace(")", "")
                .replace(" ", "")
                .replace('ae', 'ä')
                .replace('ue', 'ü')
                .replace('oe', 'ö');

       let splitted = triple_text.split("-");
       for (let i = 0; i < splitted.length; i++){
           // create nodes
           let node = JSON.parse(JSON.stringify({
                   id: splitted[i] + "_" + currentBlock,
                   name: splitted[i],
                   symbolSize: 15,
                   itemStyle: {opacity: 1, color: color_dict[currentBlock]},
                   category: Object.keys(color_dict).indexOf(currentBlock),
                   x: node_coordinates_dict[splitted[i] + "_" + currentBlock][0],
                   y: node_coordinates_dict[splitted[i] + "_" + currentBlock][1],
               }))
           if (nodes_cloned.hasOwnProperty(splitted[i] + "_" + currentBlock)) {
               delete nodes_cloned[splitted[i] + "_" + currentBlock]
               nodes_cloned[splitted[i] + "_" + currentBlock] = node
           } else {
               nodes_cloned[splitted[i] + "_" + currentBlock] = node
           }
        }

       // create curveness for links between nodes which are used multiple times
       let curveness = 0
           if (Object.keys(curveness_dict).includes(currentTriples[i])) {
               curveness = curveness_dict[currentTriples[i]]
           }
       // create link
       let link = JSON.parse(JSON.stringify(
         {source: splitted[0] + "_" + currentBlock,
               target: splitted[1] + "_" + currentBlock,
               name: currentTriples[i],
               label: { show: true, formatter: splitted[0] + " > " + splitted[1]},
               lineStyle: {opacity: 1, curveness: curveness}
               }))

        if (links_cloned.hasOwnProperty(currentTriples[i] + "_" + currentBlock)) {
               delete links_cloned[currentTriples[i] + "_" + currentBlock]
               links_cloned[currentTriples[i] + "_" + currentBlock] = link
           } else {
               links_cloned[currentTriples[i] + "_" + currentBlock] = link
           }
   }

   // create categories
   let categories = []
   for (let i = 0; i < blocks.length; i++) {
       categories[i] = JSON.parse(JSON.stringify({
           name: blocks[i],
           keyword: {},
           base: blocks[i],
           itemStyle: {color: color_dict[blocks[i]]}
           }))
    }

   // create graph object
   const graph = {
       nodes_g: Object.values(nodes_cloned),
       links_g: Object.values(links_cloned),
       categories_g: categories
   }

   return(graph);
}

/**
 * Handles the click event for edges.
 *
 * @param params params containing the information of the object which was clicked
 * @param feedback feedback function from experiment.tsx
 */
function clickEvent(params, feedback){
    if (params.dataType === "edge"){
        // get block from target string
        let block = params.data.target.split("_")[1]
        feedback(params.data.name, block)
    }
}

/**
 * Visualises the graph
 *
 * @param props parameters for graph construction
 * @returns {JSX.Element}
 */
export default function ChartB(props) {
  let blocks = []
  if (props.blockHistory.length !== 0 && props.currentBlock !== undefined) {
      // add current block to block history
      blocks = props.blockHistory.slice()
  } else {
      // just use block history
      blocks = props.blockHistory.slice()
  }

  // create graph
  const graph = createGraph(blocks, props.currentBlock, props.currentTriples,
      props.links, props.nodes)

  // click event
  const onChartClick = (params) => {
      clickEvent(params, props.feedback)
  };
  const onClick = {
      click: onChartClick,
  };

  // visualisation options
  const eChartsOption = {
  backgroundColor: "#FFFFFF",
  // title: { text: "test" },
  tooltip: {show: true},
  // grid: {show: true},
  legend: { data: blocks.reverse(),
            top: 20,
            show: true,
            selectedMode: "single"
  },
  series: [
    {
        roam: true,
        type: 'graph',
        layout: 'none',
        data: graph.nodes_g,
        links: graph.links_g,
        categories: graph.categories_g,
        label: {
          position: 'right'
        },
        // force: {
        //   edgeLength: 200,
        //   repulsion: 600,
        // },
        // animationDuration: 0,

      },
  ],

};
  return (
      <ReactEChartsCore
        style={{height: '100%', width: '100%'}}
        option={eChartsOption}
        echarts={echarts}
        onEvents={onClick}
      />
  );
}