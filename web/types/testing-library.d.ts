declare module "@testing-library/jest-dom/vitest";

declare module "@testing-library/react" {
	export const render: typeof import("@testing-library/react")['render'];
	export const screen: typeof import("@testing-library/react")['screen'];
	export const cleanup: typeof import("@testing-library/react")['cleanup'];
}

declare module "@testing-library/user-event" {
	const userEvent: typeof import("@testing-library/user-event")['default'];
	export default userEvent;
}

declare const describe: typeof import("vitest")["describe"];
declare const it: typeof import("vitest")["it"];
declare const expect: typeof import("vitest")["expect"];
