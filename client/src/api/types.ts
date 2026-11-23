import type { components } from './schema';

type Schemas = components['schemas'];

export type CaseView = Schemas['CaseView'];
export type CaseCreate = Schemas['CaseCreate'];
export type CaseCreated = Schemas['CaseCreated'];
export type CaseResume = Schemas['CaseResume'];
export type CaseResumed = Schemas['CaseResumed'];
export type CaseUpdate = Schemas['CaseUpdate'];
export type CaseSummary = Schemas['CaseSummary'];
export type DocumentView = Schemas['DocumentView'];
export type DocumentPatch = Schemas['DocumentPatch'];
export type DocumentKind = Schemas['DocumentKind'];
export type Evaluation = Schemas['Evaluation'];
export type CoverResult = Schemas['CoverResult'];
export type Flag = Schemas['Flag'];
export type Alert = Schemas['Alert'];
export type Deadline = Schemas['Deadline'];
export type ChecklistItem = Schemas['ChecklistItem'];
export type Scheme = Schemas['Scheme'];
export type SchemeInfo = Schemas['SchemeInfo'];
export type Scenario = Schemas['Scenario'];
export type Operator = Schemas['Operator'];
export type LoginRequest = Schemas['LoginRequest'];
export type LoginResponse = Schemas['LoginResponse'];
