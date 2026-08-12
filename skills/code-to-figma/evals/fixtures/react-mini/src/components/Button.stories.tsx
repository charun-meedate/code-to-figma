import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./Button";
import "../styles/button.css";

const meta: Meta<typeof Button> = {
  title: "Atoms/Button",
  component: Button,
};
export default meta;

type Story = StoryObj<typeof Button>;

export const Primary: Story = { args: { children: "Sign in", variant: "primary" } };
export const Secondary: Story = { args: { children: "Sign out", variant: "secondary" } };
export const Danger: Story = { args: { children: "Delete account", variant: "danger" } };
export const Disabled: Story = { args: { children: "Sign in", disabled: true } };
