# e2e-tests/fixtures/database/field.ts

- Field · class · L5-L17 — class Field
- constructor · method · L6-L12 — constructor( public id: number, public name: string, public type: string, public table: Table, public fieldSettings: any )
- primary · method · L14-L16 — get primary(): boolean
- createField · function · L19-L43 — async function createField( user: User, fieldName: string, type: string, fieldSettings: any, table: Table ): Promise<Field>
- updateField · function · L45-L70 — async function updateField( user: User, fieldName: string, type: string, fieldSettings: any, field: Field ): Promise<Field>
- deleteField · function · L72-L75 — async function deleteField(user: User, field: Field): Promise<void>
- getFieldsForTable · function · L77-L87 — async function getFieldsForTable( user: User, table: Table ): Promise<Field[]>
- deleteAllNonPrimaryFieldsFromTable · function · L89-L96 — async function deleteAllNonPrimaryFieldsFromTable( user: User, table: Table ): Promise<void>
