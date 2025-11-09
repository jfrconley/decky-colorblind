import {
    ButtonItem,
    PanelSection,
    PanelSectionRow,
    ToggleField,
    SliderField,
    Dropdown,
    DropdownOption,
    Field,
} from "@decky/ui";
import {
    callable,
    definePlugin,
    toaster,
} from "@decky/api";
import {useState, useEffect, FunctionComponent} from "react";
import {FaEye} from "react-icons/fa";

// TypeScript types matching Python backend
type CBType = "protanope" | "deuteranope" | "tritanope";
type Operation = "simulate" | "daltonise" | "hue_shift";

interface CorrectionConfig {
    enabled: boolean;
    cb_type: CBType;
    operation: Operation;
    strength: number;
    lut_size: number;
}

interface Result<T = null> {
    ok: boolean;
    err?: string;
    result: T;
}

// Backend callable functions
const readConfiguration = callable<[app_id: string | null], Result<CorrectionConfig>>("read_configuration");
const updateConfiguration = callable<[config: CorrectionConfig, app_id: string | null], Result>("update_configuration");
const applyConfiguration = callable<[app_id: string | null], Result>("apply_configuration");

// Dropdown options
const cbTypeOptions: DropdownOption[] = [
    {data: "protanope", label: "Protanope"},
    {data: "deuteranope", label: "Deuteranope"},
    {data: "tritanope", label: "Tritanope"},
];

const operationOptions: DropdownOption[] = [
    {data: "simulate", label: "Simulate"},
    {data: "daltonise", label: "Daltonise"},
    {data: "hue_shift", label: "Hue Shift"},
];

const Content: FunctionComponent = () => {
    // State for form values
    const [enabled, setEnabled] = useState<boolean>(true);
    const [cbType, setCbType] = useState<CBType>("deuteranope");
    const [operation, setOperation] = useState<Operation>("hue_shift");
    const [strength, setStrength] = useState<number>(1.0);

    // State for UI
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [isSaving, setIsSaving] = useState<boolean>(false);
    const [hasChanges, setHasChanges] = useState<boolean>(false);

    // TODO: Implement per-game customization
    // For now, using GLOBAL config (app_id = null)
    const currentAppId = null;

    // Load configuration on mount
    useEffect(() => {
        loadConfig();
    }, []);

    const loadConfig = async () => {
        try {
            setIsLoading(true);
            console.log("Loading configuration for app_id:", currentAppId)
            const config = (await readConfiguration(currentAppId)).result;

            console.log("Loaded configuration:", config)

            setEnabled(config.enabled);
            setCbType(config.cb_type);
            setOperation(config.operation);
            setStrength(config.strength);
            setHasChanges(false);
        } catch (error) {
            console.error("Failed to load configuration:", error);
            toaster.toast({
                title: "Error",
                body: "Failed to load configuration",
            });
        } finally {
            console.log("Finished loading configuration")
            setIsLoading(false);
        }
    };

    const handleApply = async () => {
        try {
            setIsSaving(true);

            await updateConfiguration({enabled, cb_type: cbType, operation, strength, lut_size: 32}, currentAppId);
            await applyConfiguration(currentAppId);
            setHasChanges(false);

            toaster.toast({
                title: "Success",
                body: "Colorblind correction applied",
            });
        } catch (error) {
            console.error("Failed to apply configuration:", error);
            toaster.toast({
                title: "Error",
                body: "Failed to apply configuration",
            });
        } finally {
            setIsSaving(false);
        }
    };

    // Track changes
    const markChanged = () => {
        setHasChanges(true);
    };

    if (isLoading) {
        return (
            <PanelSection>
                <PanelSectionRow>
                    <div>Loading configuration...</div>
                </PanelSectionRow>
            </PanelSection>
        );
    }

    return (
        <PanelSection>
            {/* Enable toggle */}
            <PanelSectionRow>
                <ToggleField
                    label="Enable"
                    checked={enabled}
                    onChange={(value) => {
                        setEnabled(value);
                        markChanged();
                    }}
                />
            </PanelSectionRow>

            {/* Colorblind type dropdown */}
            <PanelSectionRow>
                <Field
                    label="Colorblind Type"
                    description="Type of colorblindness to correct for"
                    childrenLayout="below"
                    childrenContainerWidth="max"
                >
                    <Dropdown
                        rgOptions={cbTypeOptions}
                        selectedOption={cbType}
                        onChange={(option) => {
                            console.log("Colorblind type changed to:", option.data);
                            setCbType(option.data as CBType);
                            markChanged();
                        }}
                    />
                </Field>
            </PanelSectionRow>

            {/* Operation mode dropdown */}
            <PanelSectionRow>
                <Field
                    label="Operation"
                    description="Type of correction to apply"
                    childrenLayout="below"
                    childrenContainerWidth="max"
                >
                    <Dropdown
                        rgOptions={operationOptions}
                        selectedOption={operation}
                        onChange={(option) => {
                            console.log("Operation changed to:", option.data);
                            setOperation(option.data as Operation);
                            markChanged();
                        }}
                    />
                </Field>
            </PanelSectionRow>

            {/* Strength slider */}
            <PanelSectionRow>
                <SliderField
                    label="Strength"
                    description="Intensity of the color correction"
                    value={strength}
                    min={0}
                    max={1}
                    step={0.1}
                    onChange={(value) => {
                        setStrength(value);
                        markChanged();
                    }}
                    showValue={true}
                />
            </PanelSectionRow>

            {/* Apply button */}
            <PanelSectionRow>
                <ButtonItem
                    layout="below"
                    onClick={handleApply}
                    disabled={isSaving || !hasChanges}
                >
                    {isSaving ? "Applying..." : hasChanges ? "Apply Changes" : "No Changes"}
                </ButtonItem>
            </PanelSectionRow>
        </PanelSection>
    );
};

export default definePlugin(() => {
    console.log("Colorblind Correction plugin initializing");

    return {
        name: "Colorblind Correction",
        titleView: <div>Colorblind Correction</div>,
        content: <Content/>,
        alwaysRender: true,
        icon: <FaEye/>,
        onDismount() {
            console.log("Colorblind Correction plugin unloading");
        },
    };
});