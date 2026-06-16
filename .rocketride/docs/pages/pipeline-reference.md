---
title: Pipeline JSON Reference
slug: /pipeline-reference
---

# Pipeline JSON Reference

A `.pipe` file is JSON conforming to the interfaces below. The schema is the
contract the [engine](/concepts/runtime-engine) loads and the SDKs send over
the [WebSocket protocol](/protocols/websocket) — the same JSON whether you
author it visually or by hand. For the concepts behind these fields, see
[Pipelines](/concepts/pipelines) and the [Execution model](/concepts/execution-model).

## Top-level shape

A pipeline is an object with a `components` array (the nodes of the graph) and,
when agents or other invokers are involved, a `control` array describing the
invoke connections. Each component declares its `id`, `provider`, `config`, and
the input lanes it consumes.

```json
{
  "components": [
    { "id": "in", "provider": "webhook", "config": {} },
    {
      "id": "out",
      "provider": "response",
      "config": { "laneName": "text" },
      "input": [{ "lane": "text", "from": "in" }]
    }
  ]
}
```

## Interfaces

The definitions below are generated from the `.pipe` schema types in
`packages/client-typescript/src/client/types/pipeline.ts`; a `.pipe` file is JSON
conforming to them.

## PipelineInputConnection

Data flow connection between pipeline components.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `lane` | `string` | Yes | Data lane/channel name (e.g., 'text', 'data', 'image') |
| `from` | `string` | Yes | Source component ID providing the data |

## PipelineControlConnection

Invoke (control-flow) connection from one component to another.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `classType` | `string` | Yes | Class type of the invoke channel (e.g., 'llm', 'tool', 'memory') |
| `from` | `string` | Yes | Source component ID providing the invocation |

## PipelineComponent

Pipeline component that processes data. Each component has a unique ID, a provider type that determines its behavior, and provider-specific configuration. Components receive data through input connections from other components.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `string` | Yes | Unique identifier for this component within the pipeline |
| `provider` | `string` | Yes | Component type/provider (e.g., 'webhook', 'response', 'ai_chat') |
| `name` | `string` | No | Human-readable component name |
| `description` | `string` | No | Component description for documentation |
| `config` | `Record<string, unknown>` | Yes | Component-specific configuration parameters |
| `ui` | `Record<string, unknown>` | No | UI-specific configuration for visual editors |
| `input` | `PipelineInputConnection[]` | No | Input connections from other components |
| `control` | `PipelineControlConnection[]` | No | Invoke (control-flow) connections from other components |

## PipelineConfig

Pipeline configuration for RocketRide data processing workflows. Defines a complete pipeline with components, data flow connections, and execution parameters. Pipelines process data through a series of connected components that transform, analyze, or route information.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `description` | `string` | No | Pipeline description |
| `version` | `number` | No | Pipeline version number |
| `components` | `PipelineComponent[]` | Yes | Array of pipeline components that process data |
| `source` | `string` | No | ID of the component that serves as the pipeline entry point |
| `project_id` | `string` | No | Project identifier for organization and permissions |
| `viewport` | `{ x: number; y: number; zoom: number }` | No | UI viewport settings for visual editors |
| `docRevision` | `number` | No | Editor document revision counter for change tracking (undo/redo, echo detection). |
| `isLocked` | `boolean` | No | Whether the canvas is locked from editing |
| `snapToGrid` | `boolean` | No | Whether node snapping to grid is enabled |
| `snapGridSize` | `[number, number]` | No | Grid size for snapping [x, y] |
| `editorMode` | `string` | No | Active editor mode (e.g. 'design', 'status', 'flow') |
